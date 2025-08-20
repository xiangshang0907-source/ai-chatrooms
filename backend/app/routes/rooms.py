"""房间管理相关的路由."""

from typing import Optional
from uuid import UUID

from flask import Blueprint, request
from flask_jwt_extended import get_current_user, jwt_required
from sqlalchemy import func
from sqlalchemy.orm import selectinload

from ..database import db
from ..models.room import Room, RoomStatus
from ..models.participant import Participant, ParticipantStatus, ParticipantType
from ..models.user import User
from ..schemas.room import (
    JoinRoomRequest,
    JoinRoomResponse,
    LeaveRoomResponse,
    RoomCreateRequest,
    RoomDetailResponse,
    RoomListResponse,
    RoomResponse,
    RoomUpdateRequest,
)
from ..services.agent_service import get_agent_service

room_blueprint = Blueprint("rooms", __name__, url_prefix="/rooms")


@room_blueprint.route("", methods=["POST"])
@jwt_required()
def create_room():
    """创建房间."""
    try:
        # 验证请求数据
        request_data = RoomCreateRequest.model_validate(request.get_json())
        current_user = get_current_user()
        
        if not current_user:
            return {"error": "unauthorized", "message": "用户未登录"}, 401
        
        # 创建房间
        room = Room(
            name=request_data.name,
            description=request_data.description,
            max_participants=request_data.max_participants,
            allow_user_interruption=request_data.allow_user_interruption,
            max_rounds_per_session=request_data.max_rounds_per_session,
            round_timeout_seconds=request_data.round_timeout_seconds,
            settings=request_data.settings,
            owner_id=current_user.id,
        )
        
        db.session.add(room)
        db.session.flush()  # 获取room.id
        
        # 自动将创建者加入房间作为房主
        participant = Participant(
            type=ParticipantType.USER,
            status=ParticipantStatus.ACTIVE,
            display_name=current_user.display_name or current_user.username,
            room_id=room.id,
            user_id=current_user.id,
        )
        
        db.session.add(participant)
        db.session.commit()
        
        # 为房间创建默认AI代理
        agent_service = get_agent_service()
        agent_service.ensure_room_has_agent(room.id, current_user.id)
        
        return RoomResponse.model_validate(room).model_dump(), 201
        
    except ValueError as e:
        db.session.rollback()
        return {"error": "validation_error", "message": str(e)}, 400
    except Exception as e:
        db.session.rollback()
        return {"error": "creation_failed", "message": "房间创建失败，请重试"}, 500


@room_blueprint.route("", methods=["GET"])
def get_rooms():
    """获取房间列表."""
    try:
        # 获取查询参数
        page = request.args.get("page", 1, type=int)
        page_size = min(request.args.get("page_size", 20, type=int), 100)
        status = request.args.get("status", RoomStatus.ACTIVE.value)
        
        # 构建查询
        query = db.session.query(Room).filter(Room.status == status)
        
        # 分页
        total = query.count()
        rooms_data = query.offset((page - 1) * page_size).limit(page_size).all()
        
        # 构建响应
        rooms = []
        for room in rooms_data:
            room_dict = RoomResponse.model_validate(room).model_dump()
            # 计算参与者数量
            participant_count = db.session.query(Participant).filter(
                Participant.room_id == room.id,
                Participant.status == ParticipantStatus.ACTIVE
            ).count()
            room_dict["participant_count"] = participant_count
            rooms.append(room_dict)
        
        return RoomListResponse(
            rooms=rooms,
            total=total,
            page=page,
            page_size=page_size,
            has_next=(page * page_size) < total,
        ).model_dump(), 200
        
    except Exception as e:
        return {"error": "fetch_failed", "message": "获取房间列表失败"}, 500


@room_blueprint.route("/<uuid:room_id>", methods=["GET"])
def get_room(room_id: UUID):
    """获取房间详情."""
    try:
        room = db.session.query(Room).options(
            selectinload(Room.participants)
        ).filter(Room.id == room_id).first()
        
        if not room:
            return {"error": "not_found", "message": "房间不存在"}, 404
        
        return RoomDetailResponse.model_validate(room).model_dump(), 200
        
    except Exception as e:
        return {"error": "fetch_failed", "message": "获取房间详情失败"}, 500


@room_blueprint.route("/<uuid:room_id>", methods=["PATCH"])
@jwt_required()
def update_room(room_id: UUID):
    """更新房间信息."""
    try:
        # 验证请求数据
        request_data = RoomUpdateRequest.model_validate(request.get_json())
        current_user = get_current_user()
        
        if not current_user:
            return {"error": "unauthorized", "message": "用户未登录"}, 401
        
        # 获取房间
        room = db.session.query(Room).filter(Room.id == room_id).first()
        if not room:
            return {"error": "not_found", "message": "房间不存在"}, 404
        
        # 检查权限（只有房主可以更新房间）
        if room.owner_id != current_user.id:
            return {"error": "forbidden", "message": "只有房主可以修改房间信息"}, 403
        
        # 更新房间信息
        update_data = request_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(room, field, value)
        
        db.session.commit()
        
        return RoomResponse.model_validate(room).model_dump(), 200
        
    except ValueError as e:
        db.session.rollback()
        return {"error": "validation_error", "message": str(e)}, 400
    except Exception as e:
        db.session.rollback()
        return {"error": "update_failed", "message": "房间更新失败，请重试"}, 500


@room_blueprint.route("/<uuid:room_id>", methods=["DELETE"])
@jwt_required()
def delete_room(room_id: UUID):
    """删除房间."""
    try:
        current_user = get_current_user()
        
        if not current_user:
            return {"error": "unauthorized", "message": "用户未登录"}, 401
        
        # 获取房间
        room = db.session.query(Room).filter(Room.id == room_id).first()
        if not room:
            return {"error": "not_found", "message": "房间不存在"}, 404
        
        # 检查权限（只有房主可以删除房间）
        if room.owner_id != current_user.id:
            return {"error": "forbidden", "message": "只有房主可以删除房间"}, 403
        
        # 删除房间（级联删除参与者和消息）
        db.session.delete(room)
        db.session.commit()
        
        return {"message": "房间删除成功", "room_id": str(room_id)}, 200
        
    except Exception as e:
        db.session.rollback()
        return {"error": "delete_failed", "message": "房间删除失败，请重试"}, 500


@room_blueprint.route("/<uuid:room_id>/join", methods=["POST"])
@jwt_required()
def join_room(room_id: UUID):
    """加入房间."""
    try:
        # 验证请求数据
        request_data = JoinRoomRequest.model_validate(request.get_json() or {})
        current_user = get_current_user()
        
        if not current_user:
            return {"error": "unauthorized", "message": "用户未登录"}, 401
        
        # 获取房间
        room = db.session.query(Room).filter(Room.id == room_id).first()
        if not room:
            return {"error": "not_found", "message": "房间不存在"}, 404
        
        # 检查房间状态
        if room.status != RoomStatus.ACTIVE:
            return {"error": "room_not_active", "message": "房间当前不可加入"}, 400
        
        # 检查是否已经是参与者
        existing_participant = db.session.query(Participant).filter(
            Participant.room_id == room_id,
            Participant.user_id == current_user.id,
            Participant.status == ParticipantStatus.ACTIVE
        ).first()
        
        if existing_participant:
            return {"error": "already_joined", "message": "您已经在该房间中"}, 400
        
        # 检查房间人数限制
        active_participants = db.session.query(Participant).filter(
            Participant.room_id == room_id,
            Participant.status == ParticipantStatus.ACTIVE
        ).count()
        
        if active_participants >= room.max_participants:
            return {"error": "room_full", "message": "房间已满"}, 400
        
        # 创建参与者
        display_name = request_data.display_name or current_user.display_name or current_user.username
        participant = Participant(
            type=ParticipantType.USER,
            status=ParticipantStatus.ACTIVE,
            display_name=display_name,
            room_id=room_id,
            user_id=current_user.id,
        )
        
        db.session.add(participant)
        db.session.commit()
        
        return JoinRoomResponse(
            participant=participant,
            room=room,
            message="成功加入房间"
        ).model_dump(), 200
        
    except ValueError as e:
        db.session.rollback()
        return {"error": "validation_error", "message": str(e)}, 400
    except Exception as e:
        db.session.rollback()
        return {"error": "join_failed", "message": "加入房间失败，请重试"}, 500


@room_blueprint.route("/<uuid:room_id>/leave", methods=["POST"])
@jwt_required()
def leave_room(room_id: UUID):
    """离开房间."""
    try:
        current_user = get_current_user()
        
        if not current_user:
            return {"error": "unauthorized", "message": "用户未登录"}, 401
        
        # 查找参与者
        participant = db.session.query(Participant).filter(
            Participant.room_id == room_id,
            Participant.user_id == current_user.id,
            Participant.status == ParticipantStatus.ACTIVE
        ).first()
        
        if not participant:
            return {"error": "not_participant", "message": "您不在该房间中"}, 400
        
        # 获取房间信息
        room = db.session.query(Room).filter(Room.id == room_id).first()
        if not room:
            return {"error": "not_found", "message": "房间不存在"}, 404
        
        # 如果是房主离开，需要特殊处理
        if room.owner_id == current_user.id:
            # 检查是否还有其他参与者
            other_participants = db.session.query(Participant).filter(
                Participant.room_id == room_id,
                Participant.user_id != current_user.id,
                Participant.status == ParticipantStatus.ACTIVE
            ).count()
            
            if other_participants > 0:
                return {
                    "error": "owner_cannot_leave", 
                    "message": "房主不能离开房间，请先删除房间或转让房主权限"
                }, 400
        
        # 更新参与者状态为离开
        participant.status = ParticipantStatus.LEFT
        db.session.commit()
        
        return LeaveRoomResponse(
            message="成功离开房间",
            room_id=room_id
        ).model_dump(), 200
        
    except Exception as e:
        db.session.rollback()
        return {"error": "leave_failed", "message": "离开房间失败，请重试"}, 500
