import sys
import logging
import structlog

from app.settings import settings


def configure_logging():
  """
  dev: 콘솔에 렌더링
  prod: JSON 로그 수집기
  """
  level = getattr(logging, settings.LOG_LEVEL, logging.INFO)
  
  logging.basicConfig(
    format="%(message)s",
    stream=sys.stdout,
    level=level,
  )
  
  shared_processors: list[structlog.types.Processor] = [
    structlog.contextvars.merge_contextvars,
    structlog.stdlib.add_log_level,
    structlog.stdlib.add_logger_name,
    structlog.processors.TimeStamper(fmt="iso"),
    structlog.processors.StackInfoRenderer(),
    structlog.processors.format_exc_info,
  ]

  if settings.is_production:
    renderer: structlog.types.Processor = structlog.processors.JSONRenderer()
  else:
    renderer: structlog.types.Processor = structlog.dev.ConsoleRenderer()
    
  structlog.configure(
    processors=[*shared_processors, renderer],
    wrapper_class=structlog.make_filtering_bound_logger(level),
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    cache_logger_on_first_use=True,
  )


def get_logger(name: str = None) -> structlog.stdlib.BoundLogger:
  return structlog.get_logger(name)