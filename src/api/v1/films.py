from http import HTTPStatus
from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.services.film import (FilmService, FilmsService, SearchService, get_film_service, get_films_service,
                               search_film_service)

router = APIRouter()


class FilmDetail(BaseModel):
    id: str
    title: str
    imdb_rating: float
    description: str
    genre: List[str]
    director: List[str]
    actors: List[Dict[str, str]]
    writers: List[Dict[str, str]]


class Films(BaseModel):
    id: str
    title: str
    imdb_rating: float


@router.get('/search',
            response_model=List[Films],
            summary='Поиск по фильмам',
            description='Полнотекстовый поиск по фильмам по описанию и названию',
            response_description='Список кинопроизведений с краткой информацией о них',
            tags=['Полнотекстовый поиск'],
            )
async def film_search(
        query: str,
        page_size: int = 50,
        page_number: int = 1,
        film_search: SearchService = Depends(search_film_service)) -> List[Films]:
    films = await film_search.search_film(query, page_size, page_number)
    if not films:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='films not found')
    return [Films(id=film.id, title=film.title, imdb_rating=film.imdb_rating) for film in films]


@router.get('/{film_id}',
            response_model=FilmDetail,
            summary='Полная информация по фильму',
            description='Получение информации о фильме',
            response_description='Полная информация по кинопроизведению',
            tags=['Фильмы'],
            )
async def film_details(
        film_id: str,
        film_service: FilmService = Depends(get_film_service)) -> FilmDetail:
    film = await film_service.get_by_id(film_id)
    if not film:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='film not found')
    return FilmDetail(id=film.id, title=film.title, imdb_rating=film.imdb_rating, description=film.description,
                      genre=film.genre, director=film.director, actors=film.actors, writers=film.writers)


@router.get('',
            response_model=List[Films],
            summary='Главная страница',
            description='Получение списка кинопроизведении с возможностью фильтрации по жанру',
            response_description='Список кинопроизведений с краткой информацией о них',
            tags=['Фильмы'],
            )
async def film_list(
        page_size: int = 50,
        page_number: int = 1,
        genre_name: str | None = None,
        films_service: FilmsService = Depends(get_films_service)) -> List[Films]:
    films = await films_service.get_films(page_size, page_number, genre_name)
    if not films:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='films over')
    return [Films(id=film.id, title=film.title, imdb_rating=film.imdb_rating) for film in films]
