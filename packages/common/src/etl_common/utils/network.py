import http.client
import logging
import random
import time

# Configuración de logging local para este módulo
logger = logging.getLogger(__name__)

# Configuración de re-intentos
MAX_RETRIES = 5
INITIAL_BACKOFF = 2
MAX_BACKOFF = 60


def execute_with_retry(func, *args, operation_name="Operation", **kwargs):
    """
    Ejecuta una función con lógica de reintento exponencial.
    """
    retry_count = 0
    backoff_time = INITIAL_BACKOFF

    while retry_count <= MAX_RETRIES:
        try:
            return func(*args, **kwargs)
        except (http.client.ResponseNotReady, http.client.HTTPException, ConnectionError, BrokenPipeError, TimeoutError) as e:
            retry_count += 1

            if retry_count > MAX_RETRIES:
                logger.error(f"❌ {operation_name} failed after {MAX_RETRIES} retries: {e}")
                raise

            # Jitter
            jitter = random.uniform(0, 0.1 * backoff_time)
            wait_time = backoff_time + jitter

            logger.warning(f"⚠️  {operation_name} failed (attempt {retry_count}/{MAX_RETRIES}): {type(e).__name__}")
            logger.warning(f"   Retrying in {wait_time:.2f} seconds...")

            time.sleep(wait_time)

            backoff_time = min(backoff_time * 2, MAX_BACKOFF)
        except Exception as e:
            logger.error(f"❌ {operation_name} failed with non-retryable error: {type(e).__name__}: {e}")
            raise
