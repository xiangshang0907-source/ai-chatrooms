"""AI代理服务模块."""

import logging
from uuid import UUID

from ..database import db
from ..models.agent import AgentProfile, ProviderType
from ..models.participant import Participant, ParticipantStatus, ParticipantType
from ..models.room import Room

logger = logging.getLogger(__name__)


class AgentService:
    """AI代理服务类."""

    @staticmethod
    def create_default_agent_for_room(room_id: UUID, creator_id: UUID) -> Participant | None:
        """
        为房间创建默认AI代理.
        
        Args:
            room_id: 房间ID
            creator_id: 创建者ID
            
        Returns:
            Participant: AI代理参与者，如果失败返回None
        """
        try:
            # 检查房间是否已有AI代理
            existing_agent = db.session.query(Participant).filter(
                Participant.room_id == room_id,
                Participant.type == ParticipantType.AGENT,
                Participant.status == ParticipantStatus.ACTIVE
            ).first()

            if existing_agent:
                logger.info(f"房间 {room_id} 已有AI代理")
                return existing_agent

            # 获取房间信息
            room = db.session.query(Room).filter(Room.id == room_id).first()
            if not room:
                logger.error(f"房间 {room_id} 不存在")
                return None

            # 创建默认AI代理配置
            agent_profile = AgentProfile(
                name=f"{room.name} - AI助手",
                description="房间的默认AI助手，可以回答问题和参与讨论",
                provider=ProviderType.QWEN,
                model_name="qwen-plus",
                system_prompt=(
                    f"你是房间「{room.name}」的AI助手。请遵循以下指导："
                    "1. 用友善、专业的语气与用户交流"
                    "2. 尽量提供有用、准确的信息"
                    "3. 如果不确定答案，请诚实说明"
                    "4. 保持对话的连贯性和上下文理解"
                    "5. 用中文回复，除非用户明确要求其他语言"
                ),
                temperature=0.7,
                max_tokens=2000,
                top_p=0.8,
                config={
                    "auto_reply": True,
                    "reply_delay": 1,  # 秒
                    "max_context_length": 10,
                },
                allowed_tools=[],
                room_id=room_id,
                created_by_id=creator_id,
            )

            db.session.add(agent_profile)
            db.session.flush()  # 获取agent_profile.id

            # 检查是否已存在相同agent_profile_id的参与者
            existing_agent_participant = db.session.query(Participant).filter(
                Participant.room_id == room_id,
                Participant.agent_profile_id == agent_profile.id,
                Participant.status == ParticipantStatus.ACTIVE
            ).first()

            if not existing_agent_participant:
                # 创建AI代理参与者
                ai_participant = Participant(
                    type=ParticipantType.AGENT,
                    status=ParticipantStatus.ACTIVE,
                    display_name=agent_profile.name,
                    room_id=room_id,
                    user_id=None,
                    agent_profile_id=agent_profile.id,
                )

                db.session.add(ai_participant)

            db.session.commit()

            logger.info(f"为房间 {room_id} 创建了默认AI代理")
            return existing_agent_participant or ai_participant

        except Exception as e:
            db.session.rollback()
            logger.error(f"创建AI代理失败: {e}")
            import traceback
            logger.error(f"详细错误信息: {traceback.format_exc()}")
            return None

    @staticmethod
    def ensure_room_has_agent(room_id: UUID, creator_id: UUID) -> bool:
        """
        确保房间有AI代理.
        
        Args:
            room_id: 房间ID
            creator_id: 创建者ID
            
        Returns:
            bool: 是否成功确保有AI代理
        """
        try:
            agent = AgentService.create_default_agent_for_room(room_id, creator_id)
            return agent is not None
        except Exception as e:
            logger.error(f"确保房间AI代理失败: {e}")
            return False


def get_agent_service() -> AgentService:
    """获取AI代理服务实例."""
    return AgentService()

