var $J1 = (function (module){
	var _p = module._p = module._p || {};

    _p.projectId = null;
    _p.loadedEntityTypesLabelMap = {};
    _p.loadedEntityTypesIdMap = {};

    _p.entity_list_init = function(projectId){
        _p.projectId = projectId;
        var data = {"project_id":projectId};


        $.when(getEntityTypeList(data))
        .done(function (entityTypeList){


            for (var k in entityTypeList.list) {
                var entityType = entityTypeList.list[k];
                _p.loadedEntityTypesLabelMap[entityType.label] = entityType;
                _p.loadedEntityTypesIdMap[entityType.id] = entityType;
            };

            resetEntityTypeList();


        });


    };

    function resetEntityTypeList(){
        var listEle = $("#entity_type_list");
        for (var k in _p.loadedEntityTypesIdMap){
            var entityType = _p.loadedEntityTypesIdMap[k];
            var itemEle = $("<tr></tr>");
            itemEle.append('<td>'+entityType.label+'</td>');

            var rolesEle = $("<td></td>");
            var rolesCount = 0;
            for (var i in entityType.sireProp.roles){
                if (rolesCount>3){
                    rolesEle.append('<div>...</div>');
                    break;
                }
                var roleId = entityType.sireProp.roles[i];
                rolesEle.append('<div>'+_p.loadedEntityTypesIdMap[roleId].label+'</div>');
                rolesCount++;
            };

            var subtypesEle = $("<td></td>");
            for (var i in entityType.sireProp.subtypes){
                var subtype = entityType.sireProp.subtypes[i];
                subtypesEle.append('<div>'+subtype+'</div>');
            };


            itemEle.append(rolesEle);
            itemEle.append(subtypesEle);
            itemEle.append('<td><a>edit</a></td>');
            listEle.append(itemEle);
        }





    }


    function getEntityTypeList(data){
        return $.ajax({
            url: Flask.url_for('typesystem.get_entity_type_list', {project_id: data.project_id})
            ,type: 'POST'
            ,contentType: "application/json;charset=utf-8"
            ,dataType: 'json'
            ,data: JSON.stringify(data)
            ,beforeSend:function(){

            }
        })
    };


	return module;
}($J1 || {}));