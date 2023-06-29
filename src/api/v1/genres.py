from http import HTTPStatus
from typing import List

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from src.services.genre import GenreService, GenresService, get_genre_service, get_genres_service

router = APIRouter()


class Genre(BaseModel):
    id: str
    name: str
    description: str


@router.get('/{genres_id}',
            response_model=Genre,
            summary='Данные по конкретному жанру',
            description='Получение информации о жанре',
            response_description='Полная информация о жанре',
            tags=['Жанры'],
            )
async def person_details(
        genres_id: str,
        genre_service: GenreService = Depends(get_genre_service)) -> Genre:
    genre = await genre_service.get_by_id(genres_id)
    if not genre:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='genre not found')
    return Genre(id=genre.id, name=genre.name)


@router.get('',
            response_model=List[Genre],
            summary='Список жанров',
            description='Получение списка жанров',
            response_description='Список жанров с краткой информацией о них',
            tags=['Жанры'],
            )
async def genre_list(
        page_size: int = 50,
        page_number: int = 1,
        genres_service: GenresService = Depends(get_genres_service)) -> List[Genre]:
    genres = await genres_service.get_genres(page_size, page_number)
    if not genres:
        raise HTTPException(status_code=HTTPStatus.NOT_FOUND, detail='genres over')
    return [Genre(id=genre.id, name=genre.name, description=genre.description) for genre in genres]
