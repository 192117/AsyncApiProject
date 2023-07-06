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
from src.models.person import Person

PERSON_CACHE_EXPIRE_IN_SECONDS = 60 * 5  # 5 минут


class PersonQuery(TypedDict):
    bool: Dict[str, Dict[str, Dict[str, str]]]


class FilmQuery(TypedDict):
    bool: Dict[str, Dict[str, Union[str, Dict[str, Dict[str, Dict[str, str]]]]]]


class PersonService:
    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

    async def get_by_id(self, person_id: str) -> Optional[Person]:
        person = await self._person_from_cache(person_id)
        if not person:
            person = await self._get_person_from_elastic(person_id)
            if not person:
                return None
            await self._put_person_to_cache(person)
        return person

    async def _get_person_from_elastic(self, person_id: str) -> Optional[Person]:
        try:
            doc = await self.elastic.get(index=config.ELASTIC_SCHEME_PERSONS, id=person_id)
        except NotFoundError:
            return None
        return Person(**doc['_source'])

    async def _get_person_from_cache(self, person_id: str) -> Optional[Person]:
        data = await self.redis.get(person_id)
        if not data:
            return None
        person = Person.parse_raw(data)
        return person

    async def _put_person_to_cache(self, person: Person):
        await self.redis.set(person.id, person.json(), PERSON_CACHE_EXPIRE_IN_SECONDS)


class SearchPersonService:
    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

    async def search_persons(self, query: str, page_size: int, page_number: int) -> Optional[Person]:
        query_search = {
            'match': {
                'full_name': {
                    'query': query,
                    'fuzziness': '2',
                },
            },
        }
        persons = await self._get_persons_from_cache(query, page_size, page_number)
        if not persons:
            persons = await self._search_persons_from_elastic(query_search, page_size, page_number)
            if not persons:
                return None
            await self._put_persons_to_cache(persons, query, page_size, page_number)
        return persons

    async def _search_persons_from_elastic(self, query_s: PersonQuery,
                                           page_size: int, page_number: int) -> Optional[List[Person]]:
        try:
            docs = await self.elastic.search(index=config.ELASTIC_SCHEME_PERSONS, query=query_s,
                                             from_=page_size * (page_number - 1), size=page_size)
        except NotFoundError:
            return None
        return [Person(**person['_source']) for person in docs['hits']['hits']]

    async def _get_persons_from_cache(self, query: str, page_size: int, page_number: int) -> Optional[List[Person]]:
        data = await self.redis.get(f'{query}-{page_size}-{page_number}')
        if not data:
            return None
        return [Person(**person) for person in orjson.loads(data)]

    async def _put_persons_to_cache(self, persons: List[Person], query: str, page_size: int, page_number: int):
        await self.redis.set(f'{query}-{page_size}-{page_number}',
                             orjson.dumps([person.dict() for person in persons]), PERSON_CACHE_EXPIRE_IN_SECONDS)


class SearchPersonFilmService:
    def __init__(self, redis: Redis, elastic: AsyncElasticsearch):
        self.redis = redis
        self.elastic = elastic

    async def search_film(self, person_id: str, page_size: int, page_number: int) -> Optional[List[Film]]:
        query_search = {
            'nested': {
                'path': 'actors',
                'query': {
                    'bool': {
                        'must': [{'match': {'actors.id': person_id}}],
                    },
                },
            },
        }
        films = await self._get_person_film_from_cache(person_id, page_size, page_number)
        if not films:
            films = await self._search_person_from_elastic(query_search, page_size, page_number)
            if not films:
                return None
            await self._put_search_person_film_to_cache(films, person_id, page_size, page_number)
        return films

    async def _search_person_from_elastic(self, query_s: FilmQuery,
                                          page_size: int, page_number: int) -> Optional[List[Film]]:
        try:
            docs = await self.elastic.search(index=config.ELASTIC_SCHEME_MOVIES, query=query_s,
                                             from_=page_size * (page_number - 1), size=page_size)
        except NotFoundError:
            return None
        return [Film(**film['_source']) for film in docs['hits']['hits']]

    async def _get_person_film_from_cache(self, person_id: str,
                                          page_size: int, page_number: int) -> Optional[List[Film]]:
        data = await self.redis.get(f'{person_id}-{page_size}-{page_number}')
        if not data:
            return None
        return [Film(**film) for film in orjson.loads(data)]

    async def _put_search_person_film_to_cache(self, films: List[Film],
                                               person_id: str, page_size: int, page_number: int):
        await self.redis.set(f'{person_id}-{page_size}-{page_number}',
                             orjson.dumps([film.dict() for film in films]), PERSON_CACHE_EXPIRE_IN_SECONDS)


@lru_cache()
def get_person_service(
        redis: Redis = Depends(get_redis),
        elastic: AsyncElasticsearch = Depends(get_elastic),
) -> PersonService:
    return PersonService(redis, elastic)


@lru_cache()
def search_person_service(
        redis: Redis = Depends(get_redis),
        elastic: AsyncElasticsearch = Depends(get_elastic),
) -> SearchPersonService:
    return SearchPersonService(redis, elastic)


@lru_cache()
def search_person_films_service(
        redis: Redis = Depends(get_redis),
        elastic: AsyncElasticsearch = Depends(get_elastic),
) -> SearchPersonFilmService:
    return SearchPersonFilmService(redis, elastic)
