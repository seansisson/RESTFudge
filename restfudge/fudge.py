import os
from flask import request, redirect, url_for, render_template, make_response
from flask_restful import Resource
from restfudge.settings import app
from restfudge.utils import switch

from imagefudge.image_fudge import Fudged, FudgeMaker


class FudgeMeta(Resource):
    """ Handles original images """
    def get(self, slug):
        if is_valid(slug):
            filename = get_file_from_slug(slug)
            headers = {'Content-Type': 'text/html'}
            return make_response(render_template(
                'image.html',
                filepath='data/'+filename,
                filename=filename
            ), 200, headers)
        else:
            return redirect(url_for('index'))


class FudgeAPIMeta(Resource):
    def get(self, slug, effect):
        ''' Returns an image if the particular effect has been applied.
        Otherwise redirects to the index page.
        '''
        if is_valid(slug) and effect is not None:
            filename = get_file_from_slug(slug, effect)
            if filename is not None:
                headers = {'Content-Type': 'text/html'}
                return make_response(render_template(
                    'image.html',
                    filepath='data/{}'.format(filename),
                    filename=filename
                ), 200, headers)
        return redirect(url_for('index'))

    def post(self, slug, effect):
        ''' Applies an effect on an image '''
        if is_valid(slug) and effect is not None:
            filename = get_file_from_slug(slug)
            ext = filename.split('.')[1]
            filename = "{}{}".format(app.config['UPLOAD_FOLDER'], filename)
            new_filename = '{slug}_{effect}.{ext}'
            new_filename = new_filename.format(slug=slug,
                                               effect=effect,
                                               ext=ext)
            args = { i:j for i,j in request.form.items() }
            fudged = self._fudge(filename, effect, args)
            fudged.save('{}{}'.format(app.config['UPLOAD_FOLDER'], new_filename))
            filename = new_filename
        headers = {'Content-Type': 'text/html'}
        return make_response(render_template(
            'image.html',
            filepath='data/{}'.format(new_filename),
            filename=filename
        ), 200, headers)

    def _fudge(self, filename, effect, kwargs):
        f = FudgeMaker(filename)
        for case in switch(effect):
            if case('draw_relative_arcs'):
                f.draw_relative_arcs(origins=kwargs['origins'],
                                     endpoints=kwargs['endpoints'],
                                     arclen=kwargs['arclen'])
                break
            elif case('fuzzy'):
                f.fuzzy(magnitude=int(kwargs['magnitude']))
                break
        return f


def get_file_from_slug(slug, effect=None):
    ''' Returns a file based on its slug '''
    files = os.listdir(app.config['UPLOAD_FOLDER'])
    if effect is None:
        search = slug
    else:
        search = "{}_{}".format(slug, effect)
    return next(filter(lambda x: search in x, files)) or None


def is_valid(slug):
    ''' Determines if a slug is valid.
    Length should be 32.
    Alpha chars should be all caps.
    File with that name should exist in upload folder.
    '''
    if len(slug) is not 32:
        return False
    if slug.upper() != slug:
        return False

    files = os.listdir(app.config['UPLOAD_FOLDER'])
    return True in list(True for filename in files if slug in filename)
