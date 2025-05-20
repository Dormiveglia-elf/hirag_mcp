"""HiRAG MCP Server"""

import asyncio
import logging
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import AsyncIterator, Optional

import numpy as np
import yaml
from hirag import HiRAG, QueryParam
from hirag._utils import compute_args_hash
from hirag.base import BaseKVStorage
from mcp.server.fastmcp import Context, FastMCP
from openai import AsyncOpenAI

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("hirag_mcp.server")

# Load configuration from YAML file
with open("config.yaml", "r") as file:
    config = yaml.safe_load(file)

# Extract configurations
OPENAI_EMBEDDING_MODEL = config["openai"]["embedding_model"]
OPENAI_MODEL = config["openai"]["model"]
OPENAI_API_KEY = config["openai"]["api_key"]
OPENAI_URL = config["openai"]["base_url"]


@dataclass
class EmbeddingFunc:
    embedding_dim: int
    max_token_size: int
    func: callable

    async def __call__(self, *args, **kwargs) -> np.ndarray:
        return await self.func(*args, **kwargs)


def wrap_embedding_func_with_attrs(**kwargs):
    """Wrap a function with attributes"""

    def final_decorator(func) -> EmbeddingFunc:
        new_func = EmbeddingFunc(**kwargs, func=func)
        return new_func

    return final_decorator


@wrap_embedding_func_with_attrs(
    embedding_dim=config["model_params"]["openai_embedding_dim"],
    max_token_size=config["model_params"]["max_token_size"],
)
async def OPENAI_embedding(texts: list[str]) -> np.ndarray:
    openai_async_client = AsyncOpenAI(base_url=OPENAI_URL, api_key=OPENAI_API_KEY)
    response = await openai_async_client.embeddings.create(
        model=OPENAI_EMBEDDING_MODEL, input=texts, encoding_format="float"
    )
    return np.array([dp.embedding for dp in response.data])


async def OPENAI_model_if_cache(
    prompt,
    system_prompt=None,
    history_messages=[],
    **kwargs,
) -> str:
    timeout = kwargs.pop("timeout", 100)
    openai_async_client = AsyncOpenAI(
        api_key=OPENAI_API_KEY, base_url=OPENAI_URL, timeout=timeout
    )
    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})

    # Get the cached response if having-------------------
    hashing_kv: BaseKVStorage = kwargs.pop("hashing_kv", None)
    messages.extend(history_messages)
    messages.append({"role": "user", "content": prompt})
    if hashing_kv is not None:
        args_hash = compute_args_hash(OPENAI_MODEL, messages)
        if_cache_return = await hashing_kv.get_by_id(args_hash)
        if if_cache_return is not None:
            return if_cache_return["return"]
    # -----------------------------------------------------

    response = await openai_async_client.chat.completions.create(
        model=OPENAI_MODEL, messages=messages, **kwargs
    )

    # Cache the response if having-------------------
    if hashing_kv is not None:
        await hashing_kv.upsert(
            {
                args_hash: {
                    "return": response.choices[0].message.content,
                    "model": OPENAI_MODEL,
                }
            }
        )
    # -----------------------------------------------------
    return response.choices[0].message.content


@asynccontextmanager
async def lifespan(_: FastMCP) -> AsyncIterator[dict]:
    """manage lifespan of HiRAG instance"""
    # global hirag_instance
    logger.info("Initializing HiRAG instance...")

    hirag_instance = HiRAG(
        working_dir=config["hirag"]["working_dir"],
        enable_llm_cache=config["hirag"]["enable_llm_cache"],
        embedding_func=OPENAI_embedding,
        best_model_func=OPENAI_model_if_cache,
        cheap_model_func=OPENAI_model_if_cache,
        enable_hierachical_mode=config["hirag"]["enable_hierachical_mode"],
        embedding_batch_num=config["hirag"]["embedding_batch_num"],
        embedding_func_max_async=config["hirag"]["embedding_func_max_async"],
        enable_naive_rag=config["hirag"]["enable_naive_rag"],
    )

    logger.info("HiRAG instance initialized successfully")
    try:
        yield {"hirag": hirag_instance}
    finally:
        logger.info("HiRAG MCP server connection closed")


mcp = FastMCP("HiRAG MCP Server", lifespan=lifespan)


@mcp.tool()
async def naive_search(
    query: str, max_tokens: Optional[int] = None, ctx: Context = None
) -> str:
    """
    Perform a naive search over the knowledge base.

    Args:
        query: The search query text
        max_tokens: Optional maximum tokens for the response

    Returns:
        The search results as text
    """
    try:
        hirag_instance = ctx.request_context.lifespan_context["hirag"]
    except Exception as e:
        logger.error(f"Error in HiRAG instance access: {e}")
        return f"{str(e)}"

    param = QueryParam(mode="naive", only_need_context=True)
    if max_tokens is not None:
        param.max_tokens = max_tokens

    result = await hirag_instance.aquery(query, param=param)

    return result


@mcp.tool()
async def hi_search(
    query: str, max_tokens: Optional[int] = None, ctx: Context = None
) -> str:
    """
    Perform a hybrid search combining both local and global knowledge over the knowledge base. (default to use)

    Args:
        query: The search query text
        max_tokens: Optional maximum tokens for the response

    Returns:
        The search results as text
    """
    try:
        hirag_instance = ctx.request_context.lifespan_context["hirag"]
    except Exception as e:
        logger.error(f"Error in HiRAG instance access: {e}")
        return f"{str(e)}"

    timeout_seconds = 100
    param = QueryParam(mode="hi", only_need_context=True, top_k=10)
    if max_tokens is not None:
        param.max_tokens = max_tokens

    try:
        result = await asyncio.wait_for(
            hirag_instance.aquery(query, param=param), timeout=timeout_seconds
        )
        return result
    except asyncio.TimeoutError:
        logger.error(f"Query timed out after {timeout_seconds} seconds")
        return f"Query timed out after {timeout_seconds} seconds. Please try a simpler query or increase the timeout."

    except Exception as e:
        logger.error(f"Error in hi_search: {e}")
        return f"Search error: {str(e)}"


if __name__ == "__main__":
    mcp.run(transport="stdio")
