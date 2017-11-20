
var $J1 = (function (module){
	var _p = module._p = module._p || {};

    _p.ml_annotator_init = function(projectId){

        _p.projectId = projectId

        data={};
        data.project_id=projectId;

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

        getSireInfo(data)
        .done(function(result){
            _p.loadedSireInfo = result.sireInfo;
            _p.resetMentionTypeClass();
        });



        setupUIEvent();

    };

    function setupUIEvent(){
        $("#documentsArea").off("click","**");
        $("#documentsArea").on("click","span, div, button",function(event){
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



    function runNeuroner(data){
        return $.ajax({
            url: Flask.url_for('annotation.run_neuroner', {project_id: data.project_id})
            ,type: 'POST'
            ,contentType: "application/json;charset=utf-8"
            ,dataType: 'json'
            ,data: JSON.stringify(data)
            ,beforeSend:function(){

            }
        })
    };

    function requestOnlineTextParser(data){
        return $.ajax({
            url: Flask.url_for('documents.online_text_parser', {project_id: data.project_id})
            ,type: 'POST'
            ,contentType: "application/json;charset=utf-8"
            ,dataType: 'json'
            ,data: JSON.stringify(data)
            ,beforeSend:function(){

            }
        })
    };

    function getRelationTypeList(data){
        return $.ajax({
            url: Flask.url_for('annotation.relationship_type_list', {project_id: data.project_id})
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
            url: Flask.url_for('annotation.entity_type_list', {project_id: data.project_id})
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
            url: Flask.url_for('annotation.ground_truth', {project_id: data.project_id})
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
            url: Flask.url_for('annotation.sire_info', {project_id: data.project_id})
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
            url: Flask.url_for('annotation.save_all_annotation', {project_id: _p.projectId})
            ,type: 'POST'
            ,contentType: "application/json;charset=utf-8"
            ,dataType: 'json'
            ,data: JSON.stringify(data)
            ,beforeSend:function(){

            }
        })
    };

    function getOnlineTextGroundTruth(data){
        return $.ajax({
            url: Flask.url_for('annotation.online_text_ground_truth', {project_id: data.project_id})
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


        };


        if (ele.is("#btnRunMLAnnotator")){
            event.stopPropagation();
            processRunMLAnnotator();
            return;

        };



    };



    function processRunMLAnnotator(){
        var sourceText = $("#document-source").val();
        sourceText = sourceText.trim();
        if (!sourceText) {
            return;
        };
        $("#document-holder").empty();
        data1={};
        data1.project_id=_p.projectId;
        data1.text = sourceText;
        requestOnlineTextParser(data1)
        .done(function(result1){

            data2={};
            data2.project_id=_p.projectId;

            getOnlineTextGroundTruth(data2)
            .done(function(result2){
                _p.loadedGroundTruth = result2.document;
                for (var k in _p.loadedGroundTruth.sentences){
                    var sentence = _p.loadedGroundTruth.sentences[k];
                    _p.sentencesIdMap[sentence.id] = sentence;
                };
                resetDocument();
                _p.resetMentionDisplay();
                _p.showLoadingProgressbar();
                runNeuroner(data1)
                .done(function(result3){
                    if (result3){
                        resetMLMentionDisplay(result3);
                    };
                })
                .always(function(message){
                    _p.hideLoadingProgressbar();
                });
            });
        });
        _p.currentToolMode = _p.toolModeEnum.mentionTool;
    };

    _p.showLoadingProgressbar = function(){
        $('#loadingWindow').empty();

        $('#loadingWindow')
            .bPopup({
                appendTo: 'body'
                ,modalColor :'WHITE'
                ,escClose  : false
                ,modalClose : false
            });

        $('<h3 id="progressbar1text"">Please Wait</h3>').appendTo('#loadingWindow');
        $('<div id="progressTimer" class="progressbar""></div>').appendTo('#loadingWindow');

        $("#progressTimer").progressTimer({
            timeLimit: 60,
            warningThreshold: 10,
            baseStyle: 'progress-bar-warning',
            warningStyle: 'progress-bar-danger',
            completeStyle: 'progress-bar-info',
            onFinish: function() {
                console.log("I'm done");
            }
        });
        $('#progressTimer').css("width",(($(window).width()/2)))
        $('#progressTimer').css("height",(($(window).height()/2)))
        $('#loadingWindow').css("left", "300px")
    };

    _p.hideLoadingProgressbar = function(){
        $('#loadingWindow').bPopup().close();
        $('#loadingWindow').empty();
    };



    function resetMLMentionDisplay(mlResult){
        for(var k in mlResult.entities){
            try{
                var entity = mlResult.entities[k];
                var from = entity.start;
                var to = entity.end;
                var label = entity.label;
                var text = entity.text;


                var sentence = _p.getTargetSentence(from,to);
                var mentionId = sentence.id+"-m"+k;
                var mention = {};

                mention.type = label;
                mention.id = mentionId;



                _p.activeSelection= {"sentenceId":sentence.id, "id":mentionId, "begin":from, "end":to, "tokens":{}};
                _p.drawMentionTargetSelection(sentence.id,from,to);
                _p.assignEntityType(mention);
            } catch (ex){
                console.log(ex);
            }


        };
        _p.clearMentionTargetSelection();
        _p.activeSelection = null;


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
            return;



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
            return;


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