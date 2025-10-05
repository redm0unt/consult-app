from typing import Optional

from flask import abort, current_app, flash, redirect, render_template, request, url_for
from flask.typing import ResponseReturnValue
from flask_login import current_user, login_required
from sqlalchemy.exc import SQLAlchemyError

from app.auth import check_rights
from app.auth.policies import BuildingsPolicy
from app.models import Building
from app.repositories import BuildingRepository, get_repository
from app.routes import bp, get_pages

building_repository: BuildingRepository = get_repository('buildings')

NAME_MAX_LENGTH = 70
ADDRESS_MAX_LENGTH = 90


@bp.route('/buildings', methods=['GET', 'POST'])
@login_required
@check_rights('buildings', 'get_page')
def buildings() -> ResponseReturnValue:
    buildings_policy = BuildingsPolicy(user_id=current_user.user_id)

    school = current_user.school
    search_query = (request.args.get('q') or '').strip()
    can_manage_buildings = buildings_policy.create()

    form_data: dict[str, str] = {}
    form_mode = 'create'
    form_building_id: Optional[int] = None
    show_building_form = False

    if request.method == 'POST':
        if not can_manage_buildings:
            abort(403)

        form_type = request.form.get('form_type') or 'create'

        if form_type == 'delete':
            building_id = request.form.get('building_id', type=int)
            if not building_id:
                flash('Не удалось определить здание для удаления', 'warning')
                return redirect(url_for('main.buildings'))

            building = building_repository.get_by_id(building_id)
            if not building or not school or building.school_id != school.school_id:
                flash('Здание не найдено или не относится к вашей школе', 'warning')
                return redirect(url_for('main.buildings'))

            try:
                building_repository.delete(building_id)
            except SQLAlchemyError:
                building_repository.rollback()
                current_app.logger.exception('Failed to delete building %s', building_id)
                flash('Не удалось удалить здание, попробуйте ещё раз позже', 'danger')
            else:
                flash('Здание успешно удалено!', 'success')
            return redirect(url_for('main.buildings'))

        name_value = (request.form.get('name') or '').strip()
        address_value = (request.form.get('address') or '').strip()

        form_data = {
            'name': name_value,
            'address': address_value,
        }

        errors: list[str] = []

        if not school:
            errors.append('Невозможно определить школу для здания — обратитесь к администратору системы')

        if not name_value:
            errors.append('Укажите название здания')
        elif len(name_value) > NAME_MAX_LENGTH:
            errors.append('Название здания не должно превышать 70 символов')

        if not address_value:
            errors.append('Укажите адрес здания')
        elif len(address_value) > ADDRESS_MAX_LENGTH:
            errors.append('Адрес здания не должен превышать 90 символов')

        building: Optional[Building] = None

        if form_type == 'update':
            form_mode = 'update'
            building_id = request.form.get('building_id', type=int)
            form_building_id = building_id
            if not building_id:
                errors.append('Не удалось определить здание для обновления')
            elif not buildings_policy.edit():
                abort(403)
            else:
                building = building_repository.get_by_id(building_id)
                if not building or not school or building.school_id != school.school_id:
                    errors.append('Здание не найдено или не относится к вашей школе')

        if errors:
            show_building_form = True
            for error in errors:
                flash(error, 'warning')
        else:
            try:
                if form_type == 'create':
                    building_repository.create(
                        school_id=school.school_id,
                        name=name_value,
                        address=address_value,
                    )
                elif form_type == 'update' and building:
                    building_repository.update(
                        building_id=building.building_id,
                        name=name_value,
                        address=address_value,
                    )
            except SQLAlchemyError:
                building_repository.rollback()
                action = 'обновить' if form_type == 'update' else 'создать'
                current_app.logger.exception('Failed to %s building', action)
                flash('Не удалось сохранить данные здания — попробуйте ещё раз позже', 'danger')
                show_building_form = True
            else:
                message = 'Здание успешно обновлено!' if form_type == 'update' else 'Здание успешно добавлено!'
                flash(message, 'success')
                return redirect(url_for('main.buildings'))

    buildings_list: list[Building] = []
    if school:
        buildings_list = building_repository.get_for_school(school.school_id, search_query or None)

    return render_template(
        'admin/buildings.html',
        page_title="Здания",
        pages=get_pages(),
        buildings=buildings_list,
        search_query=search_query,
        can_manage_buildings=can_manage_buildings,
        building_form_data=form_data,
        show_building_form=show_building_form,
        building_form_mode=form_mode,
        building_form_building_id=form_building_id,
    )
