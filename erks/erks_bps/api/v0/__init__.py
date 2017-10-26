# -*- encoding:utf-8 -*-
from flask import Blueprint, abort, Response, request
from bson import ObjectId
from json import dumps
from ercc.models import (
    Term,
    InfoType,
    GlossaryBase,
    Project,
    Glossary,
    GlossaryDerived,
    StrdTermMaster,
    InfoTypeMaster,
)

bpapp = Blueprint('api_v0', __name__)


# @bpapp.route('/dpump/strdterm/_list/<mbj:project_id>/<mbj:glossary_id>', methods=['GET', 'POST'])
# def _strd_term_list(project_id, glossary_id, check_use_pump=True):
@bpapp.route('/dpump/strdterm/_list/<mbj:project_id>/<mbj:glossary_id>', methods=['GET', 'POST'])
def _strd_term_list(project_id, glossary_id, check_use_pump=True, dbms_type='oracle', term_name=None):

    dbms_type = request.args.get('dbms_type', dbms_type)

    project = Project.objects.get_or_404(id=project_id)
    glossary = GlossaryBase.head_objects.get_or_404(id=glossary_id)

    if project != glossary.project or (check_use_pump and not glossary.use_pump):
        abort(404)

    if isinstance(glossary, Glossary):
        term_collection = Term._get_collection()
        infotype_collection = InfoType._get_collection()
        if term_name:
            term_list = term_collection.find({
                'project': ObjectId(project_id),
                'glossary': ObjectId(glossary_id),
                'term_cl_cd': 'T1',
                'published': True,
                'term_name': term_name,
            }, {
                'term_name': 1,
                'physical_term_name': 1,
                'rep_infotype': 1
            })
        else:
            term_list = term_collection.find({
                'project': ObjectId(project_id),
                'glossary': ObjectId(glossary_id),
                'term_cl_cd': 'T1',
                'published': True
            }, {
                'term_name': 1,
                'physical_term_name': 1,
                'rep_infotype': 1
            })
    elif isinstance(glossary, GlossaryDerived):
        term_collection = StrdTermMaster._get_collection()
        infotype_collection = InfoTypeMaster._get_collection()
        q = {
            'glossary_master': ObjectId(glossary.glossary_master.id),
            'project_group': ObjectId(project.project_group.id),
            '_cls': 'TermMaster.StrdTermMaster',
        }
        if term_name:
            q['term_name'] = term_name

        term_list = term_collection.find(q, {
            'term_name': 1,
            'physical_term_name': 1,
            'rep_infotype': 1
        })
    else:
        abort(400)

    def _gen():
        yield '{'
        sorry_im_bad_index = 0

        for term in term_list:
            data = {}
            data['term_name'] = term['term_name']
            data['physical_term_name'] = term['physical_term_name']
            if "rep_infotype" in term and term['rep_infotype'] is not None:
                rep_infotype = infotype_collection.find_one({'_id': term['rep_infotype']})
                data['_infotype_name'] = rep_infotype['infotype_name']
                # dbms가 여러개이면 현재로서는 용어사전에 mapping된 model을
                # 지정해주지 않으면 어떤 dbms_type을 가져와야 하는지 판단할 수가 없다.
                # if len(rep_infotype['dbms_physical_mapping_list']) >= 1:
                #     d = rep_infotype['dbms_physical_mapping_list'][0]
                #     data['_data_type'] = d['physical_type']
                # else:
                #     data['_data_type'] = ''
                for d in rep_infotype['dbms_physical_mapping_list']:
                    if d['dbms_type'] == dbms_type:
                        data['_data_type'] = d['physical_type']
                        break
            if sorry_im_bad_index > 0:
                yield ', '
            sorry_im_bad_index += 1
            yield u'"%s": %s' % (term['term_name'], dumps(data, ensure_ascii=False))
        yield '}'

    return Response(_gen(), mimetype='text/json')


@bpapp.route('/dpump/strdterm/_codelist/<mbj:project_id>/<mbj:glossary_id>', methods=['GET', 'POST'])
def _strd_term_codelist(project_id, glossary_id):

    from ercc.ercc_bps.term.models import Term
    # from ercc.ercc_bps.infotype.models import InfoType

    # project = Project.objects.get_or_404(id=project_id)
    glossary = Glossary.objects.get_or_404(id=glossary_id)

    if not glossary.use_pump:
        abort(404)

    term_collection = Term._get_collection()
    # infotype_collection = InfoType._get_collection()
    query_dict = {'project': ObjectId(project_id), 'glossary': ObjectId(glossary_id), 'term_cl_cd': 'T1', 'is_code': True, 'published': True}
    term_list = term_collection.find(query_dict)

    def _gen():
        yield '{'
        sorry_im_bad_index = 0

        for term in term_list:
            data = {}
            data['term_name'] = term['term_name']
            data['physical_term_name'] = term['physical_term_name']
            # if 'code_inherited' in term.keys():
            #     data['code_id'] = term['code_inherited']['code_id']
            #     data['code_from'] = term['code_inherited']['code_from']
            #     data['code_to'] = term['code_inherited']['code_to']
            #     data['code_instances'] = term['code_inherited']['code_instances'] if 'code_instances' in term['code_inherited'].keys() else ""
            # else:
            if True:
                data['code_id'] = term['code_id']
                data['code_from'] = term['code_from']
                data['code_to'] = term['code_to']
                data['code_instances'] = term['code_instances'] if 'code_instances' in term.keys() else ""

                # following_code_term는 objectid이기 때문에 dump시에 실패한다.
                # following_inst
                for code_instance in data['code_instances']:
                    if 'following_code_term' in code_instance:
                        del code_instance['following_code_term']
                    if 'following_inst' in code_instance:
                        del code_instance['following_inst']
            if sorry_im_bad_index > 0:
                yield ', '
            sorry_im_bad_index += 1
            yield u'"%s": %s' % (term['term_name'], dumps(data, ensure_ascii=False))
        yield '}'

    return Response(_gen(), mimetype='text/json')
