"""消息相关的路由."""

import logging
from uuid import UUID

from flask import Blueprint, Response, request
from flask_jwt_extended import get_current_user, jwt_required
from sqlalchemy import desc
from sqlalchemy.orm import selectinload

from ..database import db
from ..models.agent import AgentProfile
from ..models.conversation import ConversationRun, RunStatus
from ..models.message import Message, MessageStatus, MessageType
from ..models.participant import Participant, ParticipantStatus, ParticipantType
from ..models.room import Room
from ..schemas.message import (
    ConversationResponse,
    ConversationStartRequest,
    MessageListResponse,
    MessageResponse,
    MessageSendRequest,
)
from ..services.ai_service import AIServiceError, get_ai_service
from ..services.streaming_service import get_streaming_service

logger = logging.getLogger(__name__)

message_blueprint = Blueprint("messages", __name__, url_prefix="/rooms")


@message_blueprint.route("/<uuid:room_id>/messages", methods=["POST"])
@jwt_required()
def send_message(room_id: UUID):
    """发送消息到房间."""
    try:
        # 验证请求数据
        request_data = MessageSendRequest.model_validate(request.get_json())
        current_user = get_current_user()

        if not current_user:
            return {"error": "unauthorized", "message": "用户未登录"}, 401

        # 检查房间是否存在
        room = db.session.query(Room).filter(Room.id == room_id).first()
        if not room:
            return {"error": "room_not_found", "message": "房间不存在"}, 404

        # 检查用户是否是房间参与者
        participant = db.session.query(Participant).filter(
            Participant.room_id == room_id,
            Participant.user_id == current_user.id,
            Participant.status == ParticipantStatus.ACTIVE
        ).first()

        if not participant:
            return {"error": "not_participant", "message": "您不是该房间的参与者"}, 403

        # 获取当前房间的消息序号
        last_message = db.session.query(Message).filter(
            Message.room_id == room_id
        ).order_by(desc(Message.sequence_number)).first()

        next_sequence = (last_message.sequence_number + 1) if last_message else 1

        # 创建用户消息
        user_message = Message(
            content=request_data.content,
            type=MessageType.TEXT,
            status=MessageStatus.SENT,
            sequence_number=next_sequence,
            reply_to_id=request_data.reply_to_id,
            extra_data=request_data.extra_data,
            room_id=room_id,
            participant_id=participant.id,
        )

        db.session.add(user_message)
        db.session.flush()  # 获取消息ID

        # 异步触发AI响应（如果房间有AI代理）
        ai_message = None
        try:
            ai_message = await_ai_response(room_id, user_message.id)
        except Exception as e:
            logger.error(f"AI响应生成失败: {e}")
            # 不影响用户消息的发送

        db.session.commit()

        # 构建响应
        response_data = MessageResponse.model_validate(user_message).model_dump()

        # 如果有AI响应，一起返回
        if ai_message:
            ai_response_data = MessageResponse.model_validate(ai_message).model_dump()
            return {
                "user_message": response_data,
                "ai_message": ai_response_data,
                "message": "消息发送成功"
            }, 201

        return {"message_data": response_data, "message": "消息发送成功"}, 201

    except ValueError as e:
        db.session.rollback()
        return {"error": "validation_error", "message": str(e)}, 400
    except Exception as e:
        db.session.rollback()
        logger.error(f"发送消息失败: {e}")
        return {"error": "send_failed", "message": "消息发送失败，请重试"}, 500


@message_blueprint.route("/<uuid:room_id>/messages/stream", methods=["GET"])
@jwt_required()
def stream_messages(room_id: UUID):
    """获取房间的实时消息流."""
    try:
        current_user = get_current_user()

        if not current_user:
            return {"error": "unauthorized", "message": "用户未登录"}, 401

        # 检查房间是否存在
        room = db.session.query(Room).filter(Room.id == room_id).first()
        if not room:
            return {"error": "room_not_found", "message": "房间不存在"}, 404

        # 检查用户是否是房间参与者
        participant = db.session.query(Participant).filter(
            Participant.room_id == room_id,
            Participant.user_id == current_user.id,
            Participant.status == ParticipantStatus.ACTIVE
        ).first()

        if not participant:
            return {"error": "not_participant", "message": "您不是该房间的参与者"}, 403

        def generate():
            yield "data: {\"type\": \"connected\"}\n\n"
            # This is a placeholder - in a real app you'd implement a message queue/pubsub
            # For now, just keep the connection alive
            import time
            while True:
                yield "data: {\"type\": \"heartbeat\"}\n\n"
                time.sleep(30)

        return Response(
            generate(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Cache-Control'
            }
        )

    except Exception as e:
        logger.error(f"SSE连接失败: {e}")
        return {"error": "connection_failed", "message": "建立实时连接失败"}, 500


@message_blueprint.route("/<uuid:room_id>/messages/stream", methods=["POST"])
@jwt_required()
def send_message_stream(room_id: UUID):
    """发送消息到房间并获得流式AI响应."""
    try:
        # 验证请求数据
        request_data = MessageSendRequest.model_validate(request.get_json())
        current_user = get_current_user()

        if not current_user:
            return {"error": "unauthorized", "message": "用户未登录"}, 401

        # 检查房间是否存在
        room = db.session.query(Room).filter(Room.id == room_id).first()
        if not room:
            return {"error": "room_not_found", "message": "房间不存在"}, 404

        # 检查用户是否是房间参与者
        participant = db.session.query(Participant).filter(
            Participant.room_id == room_id,
            Participant.user_id == current_user.id,
            Participant.status == ParticipantStatus.ACTIVE
        ).first()

        if not participant:
            return {"error": "not_participant", "message": "您不是该房间的参与者"}, 403

        # 获取当前房间的消息序号
        last_message = db.session.query(Message).filter(
            Message.room_id == room_id
        ).order_by(desc(Message.sequence_number)).first()

        next_sequence = (last_message.sequence_number + 1) if last_message else 1

        # 创建用户消息
        user_message = Message(
            content=request_data.content,
            type=MessageType.TEXT,
            status=MessageStatus.SENT,
            sequence_number=next_sequence,
            reply_to_id=request_data.reply_to_id,
            extra_data=request_data.extra_data,
            room_id=room_id,
            participant_id=participant.id,
        )

        db.session.add(user_message)
        db.session.commit()

        # 返回流式响应
        def generate_stream():
            try:
                # 发送用户消息确认
                yield f"data: {{'type': 'user_message', 'id': '{user_message.id}', 'content': '{user_message.content}'}}\n\n"

                # 生成AI流式响应
                yield from generate_ai_stream_response(room_id, user_message.id)

            except Exception as e:
                logger.error(f"流式响应生成失败: {e}")
                yield "data: {'type': 'error', 'message': '流式响应生成失败'}\n\n"

        return Response(
            generate_stream(),
            mimetype='text/event-stream',
            headers={
                'Cache-Control': 'no-cache',
                'Connection': 'keep-alive',
                'Access-Control-Allow-Origin': '*',
                'Access-Control-Allow-Headers': 'Cache-Control'
            }
        )

    except ValueError as e:
        return {"error": "validation_error", "message": str(e)}, 400
    except Exception as e:
        logger.error(f"发送流式消息失败: {e}")
        return {"error": "send_failed", "message": "消息发送失败，请重试"}, 500


@message_blueprint.route("/<uuid:room_id>/messages", methods=["GET"])
@jwt_required()
def get_messages(room_id: UUID):
    """获取房间消息历史."""
    try:
        current_user = get_current_user()

        if not current_user:
            return {"error": "unauthorized", "message": "用户未登录"}, 401

        # 检查用户是否是房间参与者
        participant = db.session.query(Participant).filter(
            Participant.room_id == room_id,
            Participant.user_id == current_user.id,
            Participant.status == ParticipantStatus.ACTIVE
        ).first()

        if not participant:
            return {"error": "not_participant", "message": "您不是该房间的参与者"}, 403

        # 获取查询参数
        page = request.args.get("page", 1, type=int)
        page_size = min(request.args.get("page_size", 50, type=int), 100)

        # 构建查询
        query = db.session.query(Message).options(
            selectinload(Message.participant)
        ).filter(
            Message.room_id == room_id,
            Message.status != MessageStatus.DELETED
        ).order_by(desc(Message.created_at))

        # 分页
        total = query.count()
        messages_data = query.offset((page - 1) * page_size).limit(page_size).all()

        # 构建响应
        messages = []
        for msg in messages_data:
            msg_dict = MessageResponse.model_validate(msg).model_dump()
            messages.append(msg_dict)

        return MessageListResponse(
            messages=messages,
            total=total,
            page=page,
            page_size=page_size,
            has_next=(page * page_size) < total,
            has_prev=page > 1,
        ).model_dump(), 200

    except Exception as e:
        logger.error(f"获取消息历史失败: {e}")
        return {"error": "fetch_failed", "message": "获取消息历史失败"}, 500


@message_blueprint.route("/<uuid:room_id>/conversations", methods=["POST"])
@jwt_required()
def start_conversation(room_id: UUID):
    """开始新的对话会话."""
    try:
        # 验证请求数据
        request_data = ConversationStartRequest.model_validate(request.get_json() or {})
        current_user = get_current_user()

        if not current_user:
            return {"error": "unauthorized", "message": "用户未登录"}, 401

        # 检查房间是否存在
        room = db.session.query(Room).filter(Room.id == room_id).first()
        if not room:
            return {"error": "room_not_found", "message": "房间不存在"}, 404

        # 检查用户是否是房间参与者
        participant = db.session.query(Participant).filter(
            Participant.room_id == room_id,
            Participant.user_id == current_user.id,
            Participant.status == ParticipantStatus.ACTIVE
        ).first()

        if not participant:
            return {"error": "not_participant", "message": "您不是该房间的参与者"}, 403

        # 创建对话会话
        conversation = ConversationRun(
            name=request_data.name or f"对话 - {room.name}",
            description=request_data.description,
            status=RunStatus.RUNNING,
            total_rounds=0,
            total_tokens_used=0,
            estimated_cost=0.0,
            config_snapshot=request_data.config or {},
            room_id=room_id,
            started_by_id=current_user.id,
        )

        db.session.add(conversation)
        db.session.commit()

        return ConversationResponse.model_validate(conversation).model_dump(), 201

    except ValueError as e:
        db.session.rollback()
        return {"error": "validation_error", "message": str(e)}, 400
    except Exception as e:
        db.session.rollback()
        logger.error(f"开始对话失败: {e}")
        return {"error": "start_failed", "message": "开始对话失败，请重试"}, 500


def generate_ai_stream_response(room_id: UUID, user_message_id: UUID):
    """
    生成AI流式响应.
    
    Args:
        room_id: 房间ID
        user_message_id: 用户消息ID
    
    Yields:
        str: 流式响应数据
    """
    try:
        # 获取房间的AI代理
        ai_participant = db.session.query(Participant).filter(
            Participant.room_id == room_id,
            Participant.type == ParticipantType.AGENT,
            Participant.status == ParticipantStatus.ACTIVE
        ).first()

        if not ai_participant:
            logger.info(f"房间 {room_id} 没有活跃的AI代理")
            yield "data: {'type': 'info', 'message': '房间没有活跃的AI代理'}\n\n"
            return

        # 获取AI代理配置
        agent_profile = None
        if ai_participant.agent_profile_id:
            agent_profile = db.session.query(AgentProfile).filter(
                AgentProfile.id == ai_participant.agent_profile_id
            ).first()

        # 获取对话上下文（最近的消息）
        recent_messages = db.session.query(Message).options(
            selectinload(Message.participant)
        ).filter(
            Message.room_id == room_id,
            Message.status == MessageStatus.SENT
        ).order_by(Message.sequence_number).limit(10).all()

        # 构建对话上下文
        ai_service = get_ai_service()
        context = ai_service.build_conversation_context(recent_messages)

        # 设置系统提示词
        system_prompt = None
        if agent_profile and agent_profile.system_prompt:
            system_prompt = agent_profile.system_prompt
        else:
            system_prompt = "你是一个有用的AI助手，请用中文回答用户的问题。"

        # 获取流式服务
        streaming_service = get_streaming_service()

        # 获取下一个序号
        last_message = db.session.query(Message).filter(
            Message.room_id == room_id
        ).order_by(desc(Message.sequence_number)).first()

        next_sequence = (last_message.sequence_number + 1) if last_message else 1

        # 创建AI响应消息（初始状态）
        ai_message = Message(
            content="",  # 内容将在流式过程中更新
            type=MessageType.TEXT,
            status=MessageStatus.GENERATING,  # 生成中状态
            sequence_number=next_sequence,
            reply_to_id=user_message_id,
            extra_data={
                "ai_info": {
                    "model": "qwen-plus",
                    "streaming": True,
                }
            },
            room_id=room_id,
            participant_id=ai_participant.id,
        )

        db.session.add(ai_message)
        db.session.flush()
        ai_message_id = ai_message.id
        db.session.commit()

        # 发送AI消息开始信号
        yield f"data: {{'type': 'ai_message_start', 'id': '{ai_message_id}'}}\n\n"

        # 流式生成AI响应
        content_buffer = ""
        for chunk in streaming_service.stream_ai_response(
            messages=context,
            system_prompt=system_prompt,
            temperature=agent_profile.temperature if agent_profile else 0.7,
            max_tokens=agent_profile.max_tokens if agent_profile else 2000,
        ):
            # 转发流式数据到客户端
            yield chunk

            # 如果包含内容，更新数据库
            if chunk.startswith("data: "):
                try:
                    import json
                    data = json.loads(chunk[6:])
                    if data.get("type") == "content":
                        content_buffer += data.get("content", "")

                        # 定期更新数据库中的消息内容
                        ai_message.content = content_buffer
                        db.session.commit()

                except (json.JSONDecodeError, KeyError):
                    continue

        # 更新最终消息状态
        ai_message.content = content_buffer
        ai_message.status = MessageStatus.SENT
        db.session.commit()

        # 发送AI消息完成信号
        yield f"data: {{'type': 'ai_message_complete', 'id': '{ai_message_id}', 'content': '{content_buffer}'}}\n\n"

    except Exception as e:
        logger.error(f"生成AI流式响应失败: {e}")
        yield f"data: {{'type': 'error', 'message': '生成AI响应失败: {str(e)}'}}\n\n"


def await_ai_response(room_id: UUID, user_message_id: UUID) -> Message | None:
    """
    生成AI响应（同步版本，后续可改为异步）.
    
    Args:
        room_id: 房间ID
        user_message_id: 用户消息ID
        
    Returns:
        Message: AI响应消息，如果失败返回None
    """
    try:
        # 获取房间的AI代理
        ai_participant = db.session.query(Participant).filter(
            Participant.room_id == room_id,
            Participant.type == ParticipantType.AGENT,
            Participant.status == ParticipantStatus.ACTIVE
        ).first()

        if not ai_participant:
            logger.info(f"房间 {room_id} 没有活跃的AI代理")
            return None

        # 获取AI代理配置
        agent_profile = None
        if ai_participant.agent_profile_id:
            agent_profile = db.session.query(AgentProfile).filter(
                AgentProfile.id == ai_participant.agent_profile_id
            ).first()

        # 获取对话上下文（最近的消息）
        recent_messages = db.session.query(Message).options(
            selectinload(Message.participant)
        ).filter(
            Message.room_id == room_id,
            Message.status == MessageStatus.SENT
        ).order_by(Message.sequence_number).limit(10).all()

        # 构建对话上下文
        ai_service = get_ai_service()
        context = ai_service.build_conversation_context(recent_messages)

        # 设置系统提示词
        system_prompt = None
        if agent_profile and agent_profile.system_prompt:
            system_prompt = agent_profile.system_prompt
        else:
            system_prompt = "你是一个有用的AI助手，请用中文回答用户的问题。"

        # 生成AI响应
        ai_result = ai_service.generate_response(
            messages=context,
            system_prompt=system_prompt,
            temperature=agent_profile.temperature if agent_profile else 0.7,
            max_tokens=agent_profile.max_tokens if agent_profile else 2000,
        )

        # 获取下一个序号
        last_message = db.session.query(Message).filter(
            Message.room_id == room_id
        ).order_by(desc(Message.sequence_number)).first()

        next_sequence = (last_message.sequence_number + 1) if last_message else 1

        # 创建AI响应消息
        ai_message = Message(
            content=ai_result.content,
            type=MessageType.TEXT,
            status=MessageStatus.SENT,
            sequence_number=next_sequence,
            reply_to_id=user_message_id,
            extra_data={
                "ai_info": {
                    "model": ai_result.model_name,
                    "usage_tokens": ai_result.usage_tokens,
                    "finish_reason": ai_result.finish_reason,
                }
            },
            room_id=room_id,
            participant_id=ai_participant.id,
        )

        db.session.add(ai_message)
        return ai_message

    except AIServiceError as e:
        logger.error(f"AI服务错误: {e}")
        return None
    except Exception as e:
        logger.error(f"生成AI响应失败: {e}")
        return None
