from functools import lru_cache
from typing import Dict, List, Optional, TypedDict, Union

import orjson
from elasticsearch import AsyncElasticsearch, NotFoundError
from fastapi import Depends
from redis.asyncio import Redis

from src.core import config
from src.db.elastic import get_elastic
from src.db.redis import get_redis
from src.models.film import Film

FILM_CACHE_EXPIRE_IN_SECONDS = 60 * 5  # 5 минут


class FilterQuery(TypedDict):
    bool: Dict[str, Dict[str, List[Dict[str, Dict[str, Dict[str, str]]]]]]


class FilmQuery(TypedDict):
    bool: Dict[str, List[Dict[str, Dict[str, Dict[str, Union[str, int]]]]]]


class FilmService:
    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

    async def get_by_id(self, film_id: str) -> Optional[Film]:
        film = await self._film_from_cache(film_id)
        if not film:
            film = await self._get_film_from_elastic(film_id)
            if not film:
                return None
            await self._put_film_to_cache(film)
        return film

    async def _get_film_from_elastic(self, film_id: str) -> Optional[Film]:
        try:
            doc = await self.elastic.get(index=config.ELASTIC_SCHEME_MOVIES, id=film_id)
        except NotFoundError:
            return None
        return Film(**doc['_source'])

    async def _film_from_cache(self, film_id: str) -> Optional[Film]:
        data = await self.redis.get(film_id)
        if not data:
            return None
        film = Film.parse_raw(data)
        return film

    async def _put_film_to_cache(self, film: Film):
        await self.redis.set(film.id, film.json(), FILM_CACHE_EXPIRE_IN_SECONDS)


class FilmsService:
    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

    async def get_films(self, page_size: int, page_number: int, genre_name: Optional[str]) -> Optional[List[Film]]:
        sort_list = [
            {'imdb_rating': 'desc'},
        ]
        if genre_name:
            filter = {
                'bool': {
                    'must': [
                        {'terms': {'genre': [genre_name]}},
                    ],
                },
            }
        else:
            filter = None
        films = await self._films_from_cache(genre_name, page_size, page_number)
        if not films:
            films = await self._get_films_from_elastic(sort_list, page_size, page_number, filter)
            if not films:
                return None
            await self._put_films_to_cache(films, page_size, page_number, genre_name)
        return films

    async def _get_films_from_elastic(self, sort: List[Dict[str, str]], page_size: int, page_number: int,
                                      filter: Optional[FilterQuery]) -> Optional[List[Film]]:
        try:
            if filter:
                docs = await self.elastic.search(index=config.ELASTIC_SCHEME_MOVIES, sort=sort, query=filter,
                                                 from_=page_size * (page_number - 1), size=page_size)
            else:
                docs = await self.elastic.search(index=config.ELASTIC_SCHEME_MOVIES, sort=sort,
                                                 from_=page_size * (page_number - 1), size=page_size)
        except NotFoundError:
            return None
        return [Film(**film['_source']) for film in docs['hits']['hits']]

    async def _films_from_cache(self, genre_name: str, page_size: int, page_number: int) -> Optional[List[Film]]:
        data = await self.redis.get(f'{page_size}-{page_number}-{genre_name}')
        if not data:
            return None
        return [Film(**film) for film in orjson.loads(data)]

    async def _put_films_to_cache(self, films: List[Film], page_size: int, page_number: int, genre_name: str):
        await self.redis.set(f'{page_size}-{page_number}-{genre_name}',
                             orjson.dumps([film.dict() for film in films]), FILM_CACHE_EXPIRE_IN_SECONDS)


class SearchService:
    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

    async def search_film(self, query: str, page_size: int, page_number: int) -> Optional[List[Film]]:
        query_search = {
            'bool': {
                'should': [
                    {'match': {'title': {'query': query, 'fuzziness': 'auto'}}},
                    {'match': {'description': {'query': query, 'fuzziness': 'auto'}}},
                ],
            },
        }
        films = await self._get_films_from_cache(query, page_size, page_number)
        if not films:
            films = await self._search_film_from_elastic(query_search, page_size, page_number)
            if not films:
                return None
            await self._put_search_films_to_cache(films, query, page_size, page_number)
        return films

    async def _search_film_from_elastic(self, query_s: FilmQuery,
                                        page_size: int, page_number: int) -> Optional[List[Film]]:
        try:
            docs = await self.elastic.search(index=config.ELASTIC_SCHEME_MOVIES, query=query_s,
                                             from_=page_size * (page_number - 1), size=page_size)
        except NotFoundError:
            return None
        return [Film(**film['_source']) for film in docs['hits']['hits']]

    async def _get_films_from_cache(self, query: str, page_size: int, page_number: int) -> Optional[List[Film]]:
        data = await self.redis.get(f'{query}-{page_size}-{page_number}')
        if not data:
            return None
        return [Film(**film) for film in orjson.loads(data)]

    async def _put_search_films_to_cache(self, films: List[Film], query: str, page_size: int, page_number: int):
        await self.redis.set(f'{query}-{page_size}-{page_number}',
                             orjson.dumps([film.dict() for film in films]), FILM_CACHE_EXPIRE_IN_SECONDS)


@lru_cache()
def get_film_service(
        redis: Redis = Depends(get_redis),
        elastic: AsyncElasticsearch = Depends(get_elastic),
) -> FilmService:
    return FilmService(redis, elastic)


@lru_cache()
def get_films_service(
        redis: Redis = Depends(get_redis),
        elastic: AsyncElasticsearch = Depends(get_elastic),
) -> FilmsService:
    return FilmsService(redis, elastic)


@lru_cache()
def search_film_service(
        redis: Redis = Depends(get_redis),
        elastic: AsyncElasticsearch = Depends(get_elastic),
) -> SearchService:
    return SearchService(redis, elastic)
