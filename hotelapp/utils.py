from datetime import datetime
from itertools import groupby


def string_to_date(str):
    return datetime.strptime(str, '%Y-%m-%d').date()


def room_type_serializer(room):
    amenities = [amenity_serializer(amenity) for amenity in room.amenities]
    amenities.sort(key=lambda x: x['amenity_type'])
    grouped = {key: list(group) for key, group in groupby(
        amenities, key=lambda x: x['amenity_type'])}
    images = [image.src for image in room.images]
    return {
        "id": room.id,
        "name": room.name,
        "price": room.price,
        "room_size": room.room_size,
        "description": room.description,
        "adults": room.adults,
        "children": room.children,
        "images": images,
        "grouped": grouped,
    }


def room_serializer(room):
    return {
        "id": room.id,
        "name": room.name,
        "room_type": room.room_type,
    }


def amenity_serializer(amenity):
    return {
        "id": amenity.id,
        "name": amenity.name,
        "amenity_type": amenity.amenity_type
    }


def amenity_type_serializer(amenity):
    return {
        "id": amenity.id,
        "name": amenity.name,
    }
