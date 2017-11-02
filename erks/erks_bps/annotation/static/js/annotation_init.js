
var $J1 = (function (module){
	var _p = module._p = module._p || {};

    _p.projectId = null;

    _p.loadedEntityTypesLabelMap={};
    _p.loadedRelationTypesIdMap={};
    _p.loadedRelationPropLabelMap={};
    _p.loadedGroundTruth={};
    _p.loadedSireInfo={};
    _p.activeSelection=null;
    _p.sentencesIdMap = {};
    _p.toolModeEnum = {
        mentionTool:0,
        relationTool:1,
        coreferenceTool:2
    };
    _p.currentToolMode = null;
    _p.currentTypeSystemMode = "L"; //L ogical or P hysical

    _p.relationTargetInfo = {}

    _p.init = function(projectId,documentId){

        _p.projectId = projectId

        data={};
        data.project_id=projectId;
        data.document_id=documentId;

        _p.currentToolMode = _p.toolModeEnum.mentionTool;


        $("body").append('<div id="relationLineDrawingArea" class="relationLineDrawingArea"></div>');

        getEntityTypeList(data)
        .done(function(result){
            if (result.resultOK) {
                for (var k in result.list) {
                    var entityType = result.list[k];
                    _p.loadedEntityTypesLabelMap[entityType.label] = entityType;
                };
            } else {
                alert(result.message);
            }

            _p.resetEntityTypeList();
        });

        getRelationTypeList(data)
        .done(function(result){
            for (var k in result.list) {
                var relationType = result.list[k];
                _p.loadedRelationTypesIdMap[relationType.id] = relationType;
            };

            for (var id in _p.loadedRelationTypesIdMap){
                var relation = _p.loadedRelationTypesIdMap[id];
                //relation 은 중복되서 여러개 들어있으므로...대표되는 한개만 넣어둔다. sireprop이 나중에 사용됨.
                if (!_p.loadedRelationPropLabelMap[relation.label]){
                    _p.loadedRelationPropLabelMap[relation.label] = relation
                }
            };

            _p.resetRelationTypeList();
        });

        getGroundTruth(data)
        .done(function(result){
            _p.loadedGroundTruth = result.document;


            for (var k in _p.loadedGroundTruth.sentences){
                var sentence = _p.loadedGroundTruth.sentences[k];
                _p.sentencesIdMap[sentence.id] = sentence;
            };

            resetDocument();
            _p.resetMentionDisplay();
        });

        getSireInfo(data)
        .done(function(result){
            _p.loadedSireInfo = result.sireInfo;
            _p.resetMentionTypeClass();
        });



        setupUIEvent();

    };

    function setupUIEvent(){
        $("#document-holder").off("click","**");
        $("#document-holder").on("click","span, div",function(event){
            var ele = $(this);
            processDocumentClickEvent(ele,event);
        });

        $("#toolbar").off("click","**");
        $("#toolbar").on("click","div, button",function(event){
            var ele = $(this);
            processToolbarClickEvent(ele,event);
        });

        $("#rightSideBar").off("click","**");
        $("#rightSideBar").on("click","div, button",function(event){
            var ele = $(this);
            processRightSideBarClickEvent(ele,event);
        });

        $("#leftSideBar").off("click","**");
        $("#leftSideBar").on("click","div",function(event){
            var ele = $(this);
            processLeftSideBarClickEvent(ele,event);
        });

        $(document).bind("keydown",function(event){
            processKeyDownEvent(event);
        });

    };




    function getRelationTypeList(data){
        return $.ajax({
            url: Flask.url_for('annotation.get_relationship_type_list', {project_id: data.project_id})
            ,type: 'POST'
            ,contentType: "application/json;charset=utf-8"
            ,dataType: 'json'
            ,data: JSON.stringify(data)
            ,beforeSend:function(){

            }
        })
    };

    function getEntityTypeList(data){
        return $.ajax({
            url: Flask.url_for('annotation.get_entity_type_list', {project_id: data.project_id})
            ,type: 'POST'
            ,contentType: "application/json;charset=utf-8"
            ,dataType: 'json'
            ,data: JSON.stringify(data)
            ,beforeSend:function(){

            }
        })
    };

    function getGroundTruth(data){
        return $.ajax({
            url: Flask.url_for('annotation.get_ground_truth', {project_id: data.project_id})
            ,type: 'POST'
            ,contentType: "application/json;charset=utf-8"
            ,dataType: 'json'
            ,data: JSON.stringify(data)
            ,beforeSend:function(){

            }
        })
    };

    function getSireInfo(data){
        return $.ajax({
            url: Flask.url_for('annotation.get_sire_info', {project_id: data.project_id})
            ,type: 'POST'
            ,contentType: "application/json;charset=utf-8"
            ,dataType: 'json'
            ,data: JSON.stringify(data)
            ,beforeSend:function(){

            }
        })
    };

    function saveAll(data){
        return $.ajax({
            url: Flask.url_for('annotation.save_all', {project_id: _p.projectId})
            ,type: 'POST'
            ,contentType: "application/json;charset=utf-8"
            ,dataType: 'json'
            ,data: JSON.stringify(data)
            ,beforeSend:function(){

            }
        })
    };

    function processDocumentClickEvent(ele,event){
        if (_p.currentToolMode == _p.toolModeEnum.mentionTool){
            if (ele.hasClass("gtcToken")){
                event.stopPropagation();
                _p.processTokenSelection(ele);
            }
        };

        if (_p.currentToolMode == _p.toolModeEnum.relationTool){
            switch (_p.currentRelationToolMode){
                case _p.relationToolModeEnum.nothingSelected:
                    if (ele.hasClass("tokenEntityTypeMarker")){
                        event.stopPropagation();
                        _p.currentRelationToolMode = _p.relationToolModeEnum.parentSelected;
                        _p.relationTargetInfo.parent = ele;
                        _p.processTokenEntityTypeMarkerSelection(ele);
                        return;
                    };
                    break;
                case _p.relationToolModeEnum.parentSelected:
                    if (ele.hasClass("tokenEntityTypeMarker")){
                        event.stopPropagation();
                        if (ele.hasClass("relationTarget")){
                            _p.relationTargetInfo.child = ele;
                        };
                        _p.currentRelationToolMode = _p.relationToolModeEnum.childSelected;

                        _p.processSelectRelation(_p.relationTargetInfo);

                        return;
                    };
                    break;
                case _p.relationToolModeEnum.childSelected:

                    break;
                case _p.relationToolModeEnum.relationLabelSelected:

                    break;



            };
            //아무것도 안잡혔는데 클릭하면 nothing으로...

            _p.currentRelationToolMode = _p.relationToolModeEnum.nothingSelected;
            _p.processRelationToolUIReset();
            _p.resetRelationTypeList();
            _p.relationTargetInfo = {};


        }


    };


    function processToolbarClickEvent(ele,event){
        if (ele.is("#btnTest1")){
            var from = $("#selectionFrom").val();
            var to = $("#selectionTo").val();
            _p.drawMentionTargetSelection('s0',from,to);
            event.stopPropagation();

        };
        if (ele.is("#btnSave")){
            event.stopPropagation();
            data={};
            data.project_id=_p.projectId;
            data.ground_truth_id=_p.loadedGroundTruth.id;

            data.saveData = {};

            data.saveData.mentions = _p.loadedGroundTruth.mentions;
            data.saveData.relations = _p.loadedGroundTruth.relations;
            data.saveData.corefs = _p.loadedGroundTruth.corefs;

            console.log(data)
            saveAll(data)
            .done(function(result){

            });

        };

        if (ele.is("#btnTypeSystemLogical")){
            event.stopPropagation();
            _p.currentTypeSystemMode = "L";
            if (_p.currentToolMode == _p.toolModeEnum.mentionTool){
                _p.resetEntityTypeList();
            } else if (_p.currentToolMode == _p.toolModeEnum.relationTool){
                _p.resetRelationTypeList();
                _p.processRelationToolUIReset();
            };



        };
        if (ele.is("#btnTypeSystemPhysical")){
            event.stopPropagation();
            _p.currentTypeSystemMode = "P";
            if (_p.currentToolMode == _p.toolModeEnum.mentionTool){
                _p.resetEntityTypeList();
            } else if (_p.currentToolMode == _p.toolModeEnum.relationTool){
                _p.resetRelationTypeList();
                _p.processRelationToolUIReset();
            };


        };
    };

    function processRightSideBarClickEvent(ele,event){

        if (_p.currentToolMode == _p.toolModeEnum.mentionTool){
            if (ele.hasClass("gtcEntityType")){
                event.stopPropagation();
                _p.processEntityTypeAssignment(ele);
            };
        } else if (_p.currentToolMode == _p.toolModeEnum.relationTool){
            if (_p.currentRelationToolMode == _p.relationToolModeEnum.childSelected){
                if (ele.hasClass("gtcRelationType")){
                    event.stopPropagation();
                    _p.processRelationCreation(_p.relationTargetInfo,ele);
                    _p.currentRelationToolMode = _p.relationToolModeEnum.nothingSelected;
                    _p.processRelationToolUIReset();

                };

            }

        }


    };

    function processLeftSideBarClickEvent(ele,event){
        if (ele.is("#btnMentionTool")){
            event.stopPropagation();
            _p.processMentionToolUIReset();
        };
        if (ele.is("#btnRelationTool")){
            event.stopPropagation();
            _p.processRelationToolUIReset();
        };
        if (ele.is("#btnCoreferenceTool")){
            event.stopPropagation();

        };


    };

    function processKeyDownEvent(event){
        if (event.keyCode == 27) {
            if (_p.activeSelection) {
                _p.clearMentionTargetSelection();
                _p.activeSelection = null;

            }

        }
    };

    function resetDocument(){
        $("#document-name").empty();
        $("#document-holder").empty();
        $("#document-name").html(_p.loadedGroundTruth.name);

        for (var k in _p.loadedGroundTruth.sentences) {
            sentence = _p.loadedGroundTruth.sentences[k];
            _p.drawSentence(sentence, k);
        }
    };




    _p.getObjectId = function(obj){
        if (!obj){
            return null;
        }
        if (obj instanceof $){
            return obj.attr("id");
        } else {
            return $(obj).attr("id");
        }
    };




	return module;
}($J1 || {}));