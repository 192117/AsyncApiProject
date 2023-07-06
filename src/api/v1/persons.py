from http import HTTPStatus
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.api.v1.films import Films
from src.services.person import (PersonService, SearchPersonFilmService, SearchPersonService, get_person_service,
                                 search_person_films_service, search_person_service)

router = APIRouter()


class Film(BaseModel):
    id: str
    roles: List[str]


class Person(BaseModel):
    id: str
    full_name: str
    films: List[Film]


@router.get('/search',
            response_model=List[Person],
            summary='Поиск по персонам',
            description='Полнотекстовый поиск по персонам по полному имени',
            response_description='Список персон с краткой информацией о них',
            tags=['Полнотекстовый поиск'],
            )
async def person_search(
        query: str,
        page_size: int = 50,
        page_number: int = 1,
        person_search: SearchPersonService = Depends(search_person_service)) -> List[Person]:
    persons = await person_search.search_person(query, page_size, page_number)
    if not persons:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='persons not found')
    return [
        Person(
            id=person.id,
            full_name=person.full_name,
            films=[Film(id=film['id'], roles=film['roles']) for film in person.films],
        ) for person in persons]


@router.get('/{person_id}',
            response_model=Person,
            summary='Данные по персоне',
            description='Получение информации о персоне',
            response_description='Полная информация по персоне',
            tags=['Персоны'],
            )
async def person_details(
        person_id: str,
        person_detail: PersonService = Depends(get_person_service)) -> Person:
    person = await person_detail.get_by_id(person_id)
    if not person:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='person not found')
    return Person(id=person.id, full_name=person.full_name, films=person.films)


@router.get('/{person_id}/film',
            response_model=List[Films],
            summary='Фильмы по персоне',
            description='Поиск фильма по персоне',
            response_description='Список фильмов, в которых персона была актером с краткой информацией о них',
            tags=['Персоны'],
            )
async def person_film(
        person_id: str,
        page_size: int = 50,
        page_number: int = 1,
        person_film: SearchPersonFilmService = Depends(search_person_films_service)) -> List[Films]:
    films = await person_film.search_film(person_id, page_size, page_number)
    if not films:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='films not found')
    return [Films(id=film.id, title=film.title, imdb_rating=film.imdb_rating) for film in films]
