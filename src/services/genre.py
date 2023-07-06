from functools import lru_cache
from typing import List, Optional

import orjson
from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends
from redis.asyncio import Redis

from src.core import config
from src.db.elastic import get_elastic
from src.db.redis import get_redis
from src.models.genre import Genre

GENRE_CACHE_EXPIRE_IN_SECONDS = 60 * 5  # 5 минут


class GenreService:
    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

    async def get_by_id(self, genre_id: str) -> Optional[Genre]:
        genre = await self._get_genre_from_cache(genre_id)
        if not genre:
            genre = await self._get_genre_from_elastic(genre_id)
            if not genre:
                return None
            await self._put_genre_to_cache(genre)
        return genre

    async def _get_genre_from_elastic(self, genre_id: str) -> Optional[Genre]:
        try:
            doc = await self.elastic.get(index=config.ELASTIC_SCHEME_GENRES, id=genre_id)
        except NotFoundError:
            return None
        return Genre(**doc['_source'])

    async def _get_genre_from_cache(self, genre_id: str) -> Optional[Genre]:
        data = await self.redis.get(genre_id)
        if not data:
            return None
        genre = Genre.parse_raw(data)
        return genre

    async def _put_genre_to_cache(self, genre: Genre):
        await self.redis.set(genre.id, genre.json(), GENRE_CACHE_EXPIRE_IN_SECONDS)


class GenresService:
    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

    async def get_genres(self, page_size: int, page_number: int) -> Optional[List[Genre]]:
        genres = await self._get_genres_from_cache(page_size, page_number)
        if not genres:
            genres = await self._get_genres_from_elastic(page_size, page_number)
            if not genres:
                return None
            await self._put_genres_to_cache(genres, page_size, page_number)
        return genres

    async def _get_genres_from_elastic(self, page_size: int, page_number: int) -> Optional[List[Genre]]:
        try:
            docs = await self.elastic.search(index=config.ELASTIC_SCHEME_GENRES,
                                             from_=page_size * (page_number - 1), size=page_size)
        except NotFoundError:
            return None
        return [Genre(**genre['_source']) for genre in docs['hits']['hits']]

    async def _get_genres_from_cache(self, page_size: int, page_number: int) -> Optional[List[Genre]]:
        data = await self.redis.get(f'{page_size}-{page_number}')
        if not data:
            return None
        return [Genre(**genre) for genre in orjson.loads(data)]

    async def _put_genres_to_cache(self, genres: List[Genre], page_size: int, page_number: int):
        await self.redis.set(f'{page_size}-{page_number}',
                             orjson.dumps([genre.dict() for genre in genres]), GENRE_CACHE_EXPIRE_IN_SECONDS)


@lru_cache()
def get_genre_service(
        redis: Redis = Depends(get_redis),
        elastic: AsyncElasticsearch = Depends(get_elastic),
) -> GenreService:
    return GenreService(redis, elastic)


@lru_cache()
def get_genres_service(
        redis: Redis = Depends(get_redis),
        elastic: AsyncElasticsearch = Depends(get_elastic),
) -> GenresService:
    return GenresService(redis, elastic)
