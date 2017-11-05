var $J1 = (function (module){
	var _p = module._p = module._p || {};

	_p.resetEntityTypeDtl = function(entId){
	    var isNewEntity = false;
	    if (!entId){
            entId = _p.getUUID();
            isNewEntity = true;
	    };
        var dtlId = "dtl"+entId;
	    var dtlEle = _p.getElementFromId(dtlId);
	    if (dtlEle.length > 0){
	        var dtlDialogEle = dtlEle.closest(".ui-dialog");
            _p.focusOnObject(dtlDialogEle);
	    } else {
	        var title = "";

	        if (isNewEntity) {
	            title = "New Entity Type";
	        } else {
                if (_p.loadedEntityTypesIdMap[entId].logical_value){
                    title+=_p.loadedEntityTypesIdMap[entId].logical_value + "-";
                };
                title+=_p.loadedEntityTypesIdMap[entId].label;
	        };

            $.get(Flask.url_for('typesystem.entity_type_detail', {project_id: _p.projectId}), null, function (template) {
                $('<div id="'+dtlId+'" entityTypeId="'+entId+'"></div>').html(template)
                .dialog({
                    autoOpen: true,
                    show: "fade",
                    modal: false,
                    width: 700,
                    height: 350,
                    title: title,
                    appendTo: _p.innerMapEle,
                    close: function( event, ui ) {
                        $(this).dialog('destroy').remove();
                    },
                    focus: function( event, ui ) {
                        var maxZ = _p.getMaxEntZ();
                        $(this).closest(".ui-dialog").css("z-index",maxZ+1);
                    },
                    open: function( event, ui ) {
                        var maxZ = _p.getMaxEntZ();
                        $(this).closest(".ui-dialog").css("z-index",maxZ+1);
                        if (isNewEntity) {
                            $(this).addClass("newEntity");
                        };
                        fillEntityTypeDtlContents($(this), $(this).attr("entityTypeId"));
                        setupUIEvent($(this));
                    }
                });
            },'html');

	    };

	};


    function setupUIEvent(dtlEle){
        dtlEle.find(".entityPropertyRoleInput").off("keyup","**");
        dtlEle.find(".entityPropertyRoleInput").on("keyup",function(event){
            var ele = $(this);
            showEntityPropertyRoleList(ele,$(this).val());
        });

    };



    _p.processEntityPropertyApply = function(dtlEle){
        var entId = dtlEle.attr("entityTypeId");


        var entDtl = _p.loadedEntityTypesIdMap[entId];
        var isNewEntity = false;
        if (entDtl){


        } else {
            //new Entity
            entDtl = getBaseEntityTypeDtl();
            entDtl.id = entId;
            isNewEntity = true;
        };


        var entityPropertyLogicalNameEle = dtlEle.find(".entityPropertyLogicalName");
        var entityPropertyNameEle = dtlEle.find(".entityPropertyName");
        var entityPropertyDefEle = dtlEle.find(".entityPropertyDef");
        //loadedTypeSystemDiagram은 label을 키값으로 하기때문에...이 구조가 더 좋은지는 아직 불확실하기는 함.
        var oldLabel = entDtl.label;
        var newLabel = entityPropertyNameEle.val();

        if (entityPropertyLogicalNameEle.val()) {
            entDtl.logical_value = entityPropertyLogicalNameEle.val();
        };

        entDtl.label = newLabel;
        entDtl.definition = entityPropertyDefEle.val();
        entDtl.sireProp.roles = getEntDtlListEleRoles(dtlEle);

        if (getEntDtlListEleSubtypes(dtlEle).length > 0){
            entDtl.sireProp.subtypes = getEntDtlListEleSubtypes(dtlEle);
        } else {
            entDtl.sireProp.subtypes = null;
        }



        if (isNewEntity){

            //_p.loadedTypeSystemDiagram[entDtl.label] = {x:100, y:100};
            _p.loadedEntityTypesLabelMap[entDtl.label] = entDtl;
            _p.loadedEntityTypesIdMap[entDtl.id] = entDtl;
        };


        if (!isNewEntity && oldLabel != newLabel){
            _p.loadedEntityTypesLabelMap[newLabel] = _p.loadedEntityTypesLabelMap[oldLabel];
            delete _p.loadedEntityTypesLabelMap[oldLabel];
            _p.loadedTypeSystemDiagram[newLabel] = _p.loadedTypeSystemDiagram[oldLabel];
            delete _p.loadedTypeSystemDiagram[oldLabel];
            //_p.loadedEntityTypesIdMap[entDtl.id] = _p.loadedEntityTypesLabelMap[oldLabel];
        };
        _p.innerMapEle.empty();
        _p.resetTypeSystemDiagram();
        _p.resetMiniMap();

    };


    function getBaseEntityTypeDtl(){
        var baseEntityType = {
            alchemyAPITypes:null,
            creationDate:null,
            id:null,
            label:null,
            modifiedDate:0,
            source:null,
            typeClass:null,
            typeCreateDate:null,
            typeDesc:null,
            typeProvenance:null,
            typeSuperType:null,
            typeSuperTypeId:null,
            typeType:null,
            typeUpdateDate:null,
            typeVersion:null
        };
        baseEntityType.sireProp = {
            roles : [],
            color : "black",
            mentionType : null,
            roleOnly : false,
            clazz : null,
            active : true,
            backGroundColor : "#574A00",
            hotkey : "-",
            subtypes : null
        };
        return baseEntityType;
    };



	function fillEntityTypeDtlContents(dtlEle, entId){
	    if (dtlEle.hasClass("newEntity")){

	    } else {
	        var entDtl = _p.loadedEntityTypesIdMap[entId];

	        var entityPropertyLogicalName = entDtl.logical_value;
	        var entityPropertyName = entDtl.label;
	        var entityPropertyDef = entDtl.definition;


	        var entityPropertyLogicalNameEle = dtlEle.find(".entityPropertyLogicalName");
	        var entityPropertyNameEle = dtlEle.find(".entityPropertyName");
	        var entityPropertyDefEle = dtlEle.find(".entityPropertyDef");


	        var entityPropertySubtypesListEle = dtlEle.find(".entityPropertySubtypesList");


	        if (entityPropertyLogicalName) {
	            entityPropertyLogicalNameEle.val(entityPropertyLogicalName);
	        };
	        entityPropertyNameEle.val(entityPropertyName);
            if (entityPropertyDef) {
	            entityPropertyDefEle.val(entityPropertyDef);
	        };

            resetEntityPropertyRolesListEle(dtlEle,entDtl);
	        for (var k in entDtl.sireProp.subtypes){
	            var subtype = entDtl.sireProp.subtypes[k];
	            var subtypeEle = createNewSubtypeEle(subtype);
	            entityPropertySubtypesListEle.append(subtypeEle)
	        }

	    };

	};

	function resetEntityPropertyRolesListEle(dtlEle,entDtl){
	    var entityPropertyRolesListEle = dtlEle.find(".entityPropertyRolesList");
	    entityPropertyRolesListEle.empty();
        for (var k in entDtl.sireProp.roles){
            var roleEntId = entDtl.sireProp.roles[k];
            var roleEntDtl = _p.loadedEntityTypesIdMap[roleEntId];
            var roleEle = createNewRoleEle(roleEntDtl);
            entityPropertyRolesListEle.append(roleEle)
        };
	};

    function createNewRoleEle(roleEntDtl){
        var roleEle = $('<li class="list-group-item"><span>'+roleEntDtl.label+'</span><span class="glyphicon glyphicon-trash pull-right entityPropertyDeleteRole" aria-hidden="true"></span></li>');
        return roleEle;
    };

    function createNewSubtypeEle(text){
        var subtypeEle = $('<li class="list-group-item"><span>'+text+'</span><span class="glyphicon glyphicon-trash pull-right entityPropertyDeleteSubtype" aria-hidden="true"></span></li>');
        return subtypeEle;
    };


    function getEntDtlListEleRoles(entDltEle){
        var entDtlListRolesEle = entDltEle.find(".entityPropertyRolesList").find("li");
        var entDtlListRoles = [];
        for (var k = 0;k<entDtlListRolesEle.length;k++){
            var roleEle = $(entDtlListRolesEle[k]);
            var roleDtl = _p.loadedEntityTypesLabelMap[roleEle.text()];
            if (roleDtl) {
                entDtlListRoles.push(roleDtl.id);
            }

        };
        return entDtlListRoles;
    };

    function getEntDtlListEleSubtypes(entDltEle){
        var entDtlListSubtypesEle = entDltEle.find(".entityPropertySubtypesList").find("li");
        var entDtlListSubtypes = [];
        for (var k = 0;k<entDtlListSubtypesEle.length;k++){
            var subtypeEle = $(entDtlListSubtypesEle[k]);

            entDtlListSubtypes.push(subtypeEle.text());

        };
        return entDtlListSubtypes;
    };

    _p.toggleEntityPropertyRoleList = function(ele){
        var entDltEle = ele.closest(".ui-dialog-content");
        if (entDltEle.find(".entityPropertyRolesAddList").children("li").length < 1){
            showEntityPropertyRoleList(ele);
        } else {
            entDltEle.find(".entityPropertyRolesAddList").empty();
        }
    };


    _p.deleteEntityPropertyRole = function(ele){
        var liEle = $(ele).closest("li");
        liEle.remove();
    };

    _p.deleteEntityPropertySubtype = function(ele){
        var liEle = $(ele).closest("li");
        liEle.remove();
    };


	function showEntityPropertyRoleList(ele,keyword){
	    var entDltEle = ele.closest(".ui-dialog-content");
	    var entId = entDltEle.attr("entityTypeId");
        var entDtl = _p.loadedEntityTypesIdMap[entId];
        var entRoles = entDtl.sireProp.roles;
        var rolesToShow = [];
        var entDtlListRoles = getEntDtlListEleRoles(entDltEle);

        for (var k in _p.loadedEntityTypesIdMap){
            if ($.inArray(k, entRoles) < 0){

                if ($.inArray(k, entDtlListRoles)>-1){

                    //already in list
                } else {
                    if (keyword) {
                        if (_p.loadedEntityTypesIdMap[k].label.toUpperCase().indexOf(keyword.toUpperCase()) > -1){
                            rolesToShow.push(k);
                        }
                    } else {
                        rolesToShow.push(k);
                    };
                }

            };
        };


        entDltEle.find(".entityPropertyRolesAddList").empty();

        for (var k in rolesToShow){
            var roleId = rolesToShow[k];
            var roleLiEle = $('<li class="list-group-item">'+_p.loadedEntityTypesIdMap[roleId].label+'</li>');

            entDltEle.find(".entityPropertyRolesAddList").append(roleLiEle);
            roleLiEle.on("click",function(event){
                entDltEle.find(".entityPropertyRoleInput").val($(this).html());
                entDltEle.find(".entityPropertyRolesAddList").empty();
            });

        }

	};

    _p.addEntityPropertyRoleEle = function(ele){
        var entDtlEle = ele.closest(".ui-dialog-content");
        var entId = entDtlEle.attr("entityTypeId");
        var entDtl = _p.loadedEntityTypesIdMap[entId];
        var entRoles = entDtl.sireProp.roles;
        var roleInputEle = entDtlEle.find(".entityPropertyRoleInput");
        var roleToAdd = _p.loadedEntityTypesLabelMap[roleInputEle.val()];
        if (roleToAdd){
            if ($.inArray(roleToAdd.id, entRoles) < 0){


                var roleEle = createNewRoleEle(roleToAdd);
                entDtlEle.find(".entityPropertyRolesList").append(roleEle)
                //entRoles.push(roleToAdd.id)

            }

        };
        //resetEntityPropertyRolesListEle(entDltEle,entDtl);

    };

    _p.addEntityPropertySubtype = function(ele){
        var entDtlEle = ele.closest(".ui-dialog-content");
        var entId = entDtlEle.attr("entityTypeId");
        var entDtl = _p.loadedEntityTypesIdMap[entId];
        var subtypeInputEle = entDtlEle.find(".entityPropertySubtypeInput");
        var entDtlListSubtypes = getEntDtlListEleSubtypes(entDtlEle);
        var inputText = subtypeInputEle.val();
        if (inputText){
            if ($.inArray(inputText, entDtlListSubtypes) < 0){
                entDtlEle.find(".entityPropertySubtypesList").append(createNewSubtypeEle(inputText));
            }
        }
    };




	_p.resetRelationTypeDtl = function(sourceId, targetId){
	    var isNewRelation = false;

        var dtlId = "dtl"+sourceId+"-"+targetId;
	    var dtlEle = _p.getElementFromId(dtlId);

	    if (dtlEle.length > 0){
	        var dtlDialogEle = dtlEle.closest(".ui-dialog");
            _p.focusOnObject(dtlDialogEle);
	    } else {
	        var title = "Relation Property";


            $.get(Flask.url_for('typesystem.relation_type_detail', {project_id: _p.projectId}), null, function (template) {
                $('<div id="'+dtlId+'" sourceEntityTypeId="'+sourceId+'" targetEntityTypeId="'+targetId+'"></div>').html(template)
                .dialog({
                    autoOpen: true,
                    show: "fade",
                    modal: false,
                    width: 700,
                    height: 350,
                    title: "New Relation Type",
                    appendTo: _p.innerMapEle,
                    close: function( event, ui ) {
                        $(this).dialog('destroy').remove();
                    },
                    focus: function( event, ui ) {
                        var maxZ = _p.getMaxEntZ();
                        $(this).closest(".ui-dialog").css("z-index",maxZ+1);
                    },
                    open: function( event, ui ) {
                        var maxZ = _p.getMaxEntZ();
                        $(this).closest(".ui-dialog").css("z-index",maxZ+1);
                        fillRelationTypeDtlContents($(this), sourceId, targetId);
                    }
                });
            },'html');

	    };


	};



	function fillRelationTypeDtlContents(dtlEle, sourceId, targetId){

        var sourceEntDtl = _p.loadedEntityTypesIdMap[sourceId];
        var targetEntDtl = _p.loadedEntityTypesIdMap[targetId];

        var relationPropertyLogicalNameEle = dtlEle.find(".relationPropertyLogicalName");
        var relationPropertyNameEle = dtlEle.find(".relationPropertyName");
        var relationPropertyDefEle = dtlEle.find(".relationPropertyDef");
        var relationPropertySourceEle = dtlEle.find(".relationPropertySource");
        var relationPropertyTargetEle = dtlEle.find(".relationPropertyTarget");

        //var relDtl = _p.loadedRelationTypesIdMap[relId];

        var relationPropertyEntityRelationsListEle = dtlEle.find(".relationPropertyEntityRelationsList");
        relationPropertyEntityRelationsListEle.empty();
        var srcTgtrelations = null;
        if (_p.loadedSrcTgtRelationMap[sourceId+"-"+targetId]){
            srcTgtrelations = _p.loadedSrcTgtRelationMap[sourceId+"-"+targetId].relations;
        };
        var srcTgtRelationsLabels = [];
        for (var k in srcTgtrelations){
            var relDtl = srcTgtrelations[k];
            var relationItem = $('<li class="list-group-item small-list-group-item"><span class="relationPropertyEntityRelation" relId="'+relDtl.id+'">'+relDtl.label+'</span><span class="glyphicon glyphicon-trash pull-right relationPropertyDeleteRelation" aria-hidden="true" relId="'+relDtl.id+'"></span></li>');



            srcTgtRelationsLabels.push(relDtl.label);
            relationPropertyEntityRelationsListEle.append(relationItem);
        };


        var relationPropertyAllRelationsListEle = dtlEle.find(".relationPropertyAllRelationsList");
        relationPropertyAllRelationsListEle.empty();

        var allRelationsToShow=[];

        for (var k in _p.loadedRelationTypesLabelMap){


            if (srcTgtRelationsLabels.indexOf(k) > -1){

            } else {
                var relDtl = _p.loadedRelationTypesLabelMap[k];
                var relationItem = $('<div class="list-group-item small-list-group-item relationPropertyAllRelation" relId="'+relDtl.id+'">'+relDtl.label+'</div>');
                relationPropertyAllRelationsListEle.append(relationItem);

            }

        };






/*
        if (relDtl) {
            relationPropertyNameEle.val(relDtl.label);
        }
*/

        relationPropertySourceEle.val(sourceEntDtl.label);
        relationPropertyTargetEle.val(targetEntDtl.label);

	};

    _p.deleteEntityRelation = function(ele){
        var relId = ele.attr("relId");
        delete _p.loadedRelationTypesIdMap[relId];

        _p.resetRelationMaps();

        _p.resetTypeSystemDiagram();
    };

    _p.selectAllRelation= function(relationItemEle){
        var relId = relationItemEle.attr("relId");
        var dtlEle = relationItemEle.closest(".ui-dialog-content");
        dtlEle.find(".active").each(function(index,ele){
            $(ele).removeClass("active");
        });
        relationItemEle.addClass("active");

        var relDtl = _p.loadedRelationTypesIdMap[relId];
        var relationPropertyLogicalNameEle = dtlEle.find(".relationPropertyLogicalName");
        var relationPropertyNameEle = dtlEle.find(".relationPropertyName");
        var relationPropertyDefEle = dtlEle.find(".relationPropertyDef");
        relationPropertyLogicalNameEle.val()


        if (relDtl.logical_value) {
            relationPropertyLogicalNameEle.val(relDtl.logical_value);
        };

        relationPropertyNameEle.val(relDtl.label);
        relationPropertyDefEle.val(relDtl.definition);




    };


    _p.selectEntityRelation= function(relationItemEle){
        var relId = relationItemEle.attr("relId");
        var dtlEle = relationItemEle.closest(".ui-dialog-content");
        dtlEle.find(".active").each(function(index,ele){
            $(ele).removeClass("active");
        });
        relationItemEle.parent().addClass("active");


        var relDtl = _p.loadedRelationTypesIdMap[relId];
        var relationPropertyLogicalNameEle = dtlEle.find(".relationPropertyLogicalName");
        var relationPropertyNameEle = dtlEle.find(".relationPropertyName");
        var relationPropertyDefEle = dtlEle.find(".relationPropertyDef");
        relationPropertyLogicalNameEle.val()


        if (relDtl.logical_value) {
            relationPropertyLogicalNameEle.val(relDtl.logical_value);
        };

        relationPropertyNameEle.val(relDtl.label);
        relationPropertyDefEle.val(relDtl.definition);


    };


    function getBaseRelationTypeDtl(){
        var baseRelationType = {
            creationDate:null,
            id:null,
            label:null,
            modifiedDate:0,
            source:0,
            srcEntType:null,
            tgtEntType:null,
            typeClass:null,
            typeCreateDate:null,
            typeDesc:null,
            typeProvenance:null,
            typeSuperType:null,
            typeType:null,
            typeUpdateDate:null,
            typeVersion:null
        };
        baseRelationType.sireProp = {
            active : true,
            backGroundColor : "#EFC100",
            clazz : null,
            color : "#000000",
            hotkey : null,
            modality : null,
            tense : null
        };
        return baseRelationType;
    };





    _p.processRelationPropertyApply = function(dtlEle){
        var sourceEntId = dtlEle.attr("sourceEntityTypeId");
        var targetEntId = dtlEle.attr("targetEntityTypeId");


        var relationPropertyNameEle = dtlEle.find(".relationPropertyName");
        var relDtl = _p.loadedRelationTypesLabelMap[relationPropertyNameEle.val()];
        var isNewRelation = false;

        if (relDtl){

        } else {
            //new Entity
            relDtl = getBaseRelationTypeDtl();


            relDtl.id = _p.getUUID();
            relDtl.srcEntType = sourceEntId;
            relDtl.tgtEntType = targetEntId;
            isNewRelation = true;
        };


        var relationPropertyLogicalNameEle = dtlEle.find(".relationPropertyLogicalName");
        var relationPropertyNameEle = dtlEle.find(".relationPropertyName");
        var relationPropertyDefEle = dtlEle.find(".relationPropertyDef");

        var oldLabel = relDtl.label;
        var newLabel = relationPropertyNameEle.val();
        if (relationPropertyLogicalNameEle.val()) {
            relDtl.logical_value = relationPropertyLogicalNameEle.val();
        };

        relDtl.label = newLabel;
        relDtl.definition = relationPropertyDefEle.val();


        if (isNewRelation){
            //_p.loadedTypeSystemDiagram[entDtl.label] = {x:100, y:100};
            _p.loadedRelationTypesIdMap[relDtl.id] = relDtl;
            _p.loadedRelationTypesLabelMap[relDtl.label] = relDtl;
        };



        if (!isNewRelation && oldLabel != newLabel){
            _p.loadedRelationTypesLabelMap[newLabel] = _p.loadedRelationTypesLabelMap[oldLabel];
            delete _p.loadedRelationTypesLabelMap[oldLabel];

        };


        _p.resetRelationMaps();

        _p.resetTypeSystemDiagram();

        var srcTgtRelationId = sourceEntId + "-" + targetEntId
        var srcTgtRelation = _p.loadedSrcTgtRelationMap[srcTgtRelationId];

        _p.drawRelation(srcTgtRelation);

    };






	return module;
}($J1 || {}));