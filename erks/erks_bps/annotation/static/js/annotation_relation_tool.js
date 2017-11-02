
var $J1 = (function (module){
	var _p = module._p = module._p || {};


    _p.relationToolModeEnum = {
        nothingSelected:0,
        parentSelected:1,
        childSelected:2,
        relationLabelSelected:3
    };

    _p.currentRelationToolMode = _p.relationToolModeEnum.nothingSelected;


    _p.processRelationToolUIReset = function(){
        $("#relationToolRightSideBar").css("display","");
        $("#mentionToolRightSideBar").css("display","none");
        activateRelationToolDocumentUI();
        _p.currentRelationToolMode = _p.relationToolModeEnum.nothingSelected;

    };

    _p.resetRelationTypeList = function(list){
        $("#list-relation-type").empty();
        if (!list) {
            list = _p.loadedRelationPropLabelMap;
        };

        var labelMap = {};

        for (var id in list){
            var relation = list[id];
            if (relation.label in labelMap){

            } else {
                drawRelationTypeItem(relation);
                labelMap[relation.label] = 1;
            }


        };

    };

    function activateRelationToolDocumentUI(){
        _p.currentToolMode = _p.toolModeEnum.relationTool;
        _p.clearRelationDrawingArea();
        $("#document-holder").find(".gtcSentence").each(function(index,ele){
            var ele = $(ele);
            resetRelationDrawingArea(ele);
        });


        //여기서, 읽어온 relation 을 그려주는 작업을 해야한다.
        _p.resetRelationDisplay();

        _p.clearMentionTargetSelection();
        _p.activeSelection = null;
    };

    _p.clearRelationDrawingArea = function(){
        $("#document-holder").find(".tokenEntityTypeMarker").each(function(index,ele){
            ele = $(ele);
            ele.remove();

        });
        $("#document-holder").find(".relationLabel").remove();
        $("#document-holder").find(".relationTarget").each(function(index,ele){
            ele = $(ele);
            ele.removeClass("relationTarget");

        });
        jsPlumb.deleteEveryConnection();
    }



    function resetRelationDrawingArea(sentenceEle){

        //목적은 한 행당 하나씩 Padding을 넣어두는것.
        //padding 에서 height 로 변경. 이게 계산하기 편함.

        var lastTop = null;
        var paddingCount = 0;
        var lastMentionId = null;
        sentenceEle.find(".gtcToken").each(function(index,ele){
            ele = $(ele);
            if (ele.hasClass("entityTypeAssigned")){

                addRelationAreaPadding(sentenceEle,ele);

                //색깔 등을 지움.
                ele.css("background-color","");
                ele.css("color","");

                var mentionId = ele.attr("mentionId");
                if (mentionId != lastMentionId){
                    addTokenEntityTypeMarker(sentenceEle,ele);
                    lastMentionId = mentionId;
                }
            }

        });
    };

    function addTokenEntityTypeMarker(sentenceEle,tokenEle){
        var entityTypeLabel = tokenEle.attr("entityTypeLabel");
        var entityType = _p.loadedEntityTypesLabelMap[entityTypeLabel];

        if (_p.currentTypeSystemMode == "L" && entityType.logical_value) {
            entityTypeLabel = entityType.logical_value;
        };

        var tokenEntityTypeMarker = $('<div class="tokenEntityTypeMarker" data-toggle="tooltip" title="'+entityTypeLabel+'">'+entityTypeLabel+'</div>');
        tokenEntityTypeMarker.css("background-color",entityType.sireProp.backGroundColor);
        tokenEntityTypeMarker.css("color",entityType.sireProp.color);
        tokenEntityTypeMarker.css("border-color",entityType.sireProp.backGroundColor);
        sentenceEle.append(tokenEntityTypeMarker);
        tokenEntityTypeMarker.css("left",tokenEle.position().left);
        tokenEntityTypeMarker.css("top",tokenEle.position().top-30);
        //줄바뀜 있을때 버그가 있음
        //tokenEntityTypeMarker.css("width",tokenEle.width());
        tokenEntityTypeMarker.css("width",tokenEle.find(".gtcTokenText").width());

        tokenEntityTypeMarker.attr("mentionId",tokenEle.attr("mentionId"));
        tokenEntityTypeMarker.attr("entityTypeLabel",tokenEle.attr("entityTypeLabel"));

    };

    function addRelationAreaPadding(sentenceEle,tokenEle){
        //약간 비효율적으로 보이지만, 만들기 쉽게 하기 위해...
        //일단 한개 넣어놔보고, 이전것과 높이가 같으면 필요없구나...하고 다시 제거하는 로직으로 간다.

        //그래야 나중에 높이 변할때 한개만 바꿔도 실제 간격이 변하게 할 수 있다.
        //일단 일정한 간격으로 무조건 늘려준다.
        var newEle = $('<span class="gtcTokenRelationMargin"></span>');

        if (tokenEle.find(".gtcTokenRelationMargin").length < 1){
            tokenEle.append(newEle);
            var newEleTop = newEle.offset().top;
            sentenceEle.find(".gtcTokenRelationMargin").each(function(index,ele){
                var isNewMarginNeeded = true;
                var eleTop = $(ele).offset().top;
                if ( !newEle.is(ele) && Math.abs(eleTop - newEleTop) < 100){
                    //이러면 같은줄에 이미 margin 이 있는걸로 판정.
                    newEle.remove();
                } else {

                }
            });
        }


    };

    function recalcRelationAreaPadding(sentenceEle){

    //사용안됨
        //같은줄에 relationLabel 이 몇개나 있는지 보고 이에따라 gtcTokenRelationMargin의 높이를 조절해 준다.
        sentenceEle.find(".gtcTokenRelationMargin").each(function(index,marginEle){
            var marginBotton = $(marginEle).offset().top + $(marginEle).height();
            console.log(marginEle)
            sentenceEle.find(".relationLabel").each(function(i,relationLabelEle){

                //이거 좀 이상함. class를 지정해 주려니 jquery에서 검색이 안됨.

                //var getToken = sentenceEle.find('.gtcToken span[mentionId="'+$(e).attr("parentMentionId")+'"]');
                var gtcToken = sentenceEle.find('span[mentionId="'+$(relationLabelEle).attr("parentMentionId")+'"]');
                var getTokenTop = gtcToken.offset().top;
                var getTokenBottom = getTokenTop + gtcToken.height();
                if (marginBotton <= getTokenBottom && getTokenBottom > getTokenTop){
                    //이러면, 지금 이 relationLabelEle 이 marginEle 의 관할하인녀석이다.

                    console.log(relationLabelEle)
                }

            });

        });




    }

    function recalcRelationAreaPadding1(lineMarginGroupInfo){
        if (lineMarginGroupInfo.length > 0){
        //console.log(lineMarginGroupInfo)
        }
        //{"paddingEleContainer":gtcToken , "relationLabels":[]};

        for (var k in lineMarginGroupInfo){
            var marginGroup = lineMarginGroupInfo[k];


            var marginEle = marginGroup.paddingEle;

            //console.log(marginEle.offset().top);
            //console.log(marginGroup.relationLabels[0].offset().top)

            for (var i in marginGroup.relationLabels){
                var relationLabel = marginGroup.relationLabels[i];
                if (marginEle.offset().top > relationLabel.offset().top+20){
                    var diff = marginEle.offset().top - relationLabel.offset().top;

                    //갑자기 넓이가 확 넓어지는 버그때문에 땜빵. 나중에 새로 만들어야함.
                    if (diff > 100) {continue;}
                    var newMargin = marginEle.height() + diff;

                    marginEle.css("height",newMargin);
                    activateRelationToolDocumentUI();
                    break;

                }
            }

        }


    }

    function drawRelationTypeItem(item){
        var style = "border-color:" + item.sireProp.backGroundColor + "; color:"+item.sireProp.color;
        var hotkey = item.sireProp.hotkey;
        if (!hotkey) {
            hotkey = "-";
        };

        var label = item.label;
        if (_p.currentTypeSystemMode == "L" && item.logical_value) {
            label = item.logical_value;
        };


        var itemEle = $('<div gtcRelationLabel="'+item.label+'" id="'+item.id+'" class="gtcRelationType"><div class="itemRelationIcon" style="'+style+'">'+hotkey+'</div><div class="itemLabel">'+label+'</div></div>');
        $("#list-relation-type").append(itemEle);
    };

    _p.resetRelationDisplay = function(){
        $("#document-holder").find(".gtcSentence").each(function(index,ele){
            _p.resetSentenceRelationDisplay($(ele));
        });
    }

    _p.resetSentenceRelationDisplay = function(sentenceEle){


        //var relations = _p.loadedGroundTruth.relations;
        var relationLabelStackCount = 1;
        var lastMarkerTop = null;
        //console.log(relations)

        var lineIndex = 0;
        var lineMarginGroupInfo = {};
        var marginContainer = null;
        //선 그리기 문제때문에 relation 순서대로 하면 안된다.
        //mention이 포착되는 순서대로 그에따른 relation 을 처리해 줘야한다.
        var marginEle = null;
        sentenceEle.find(".tokenEntityTypeMarker").each(function(index,ele){
            ele = $(ele);
            var mentionId = ele.attr("mentionId");

            var marginContainer = sentenceEle.find('span[mentionId="'+mentionId+'"]');
            if (marginContainer.find(".gtcTokenRelationMargin").length > 0){
                marginEle = $(marginContainer.find(".gtcTokenRelationMargin")[0]);
            };




            //우선 tokenEntityTypeMarker 하나를 고른다음, 그놈에게 속한 relation들을 가져와서,
            var relations = $.grep(_p.loadedGroundTruth.relations, function(e){ return e.args[0] == mentionId; });
            //relation 을 그린다.

            for (var k in relations){
                var relation = relations[k];
                var parentMarkerId = relation.args[0];
                var childMarkerId = relation.args[1]

                var parentMarkerEle = $($('div[mentionId="'+parentMarkerId+'"]')[0]);

                var childMarkerEle = $($('div[mentionId="'+childMarkerId+'"]')[0]);
                //var sentenceEle = $(parentMarkerEle.closest(".gtcSentence"));
                var relationType = _p.loadedRelationPropLabelMap[relation.type];

                var label = relation.type;
                if (_p.currentTypeSystemMode == "L" && relationType.logical_value) {
                    label = relationType.logical_value;
                };

                var relationLabelEle = $('<div class="relationLabel">'+label+'</div>');

                relationLabelEle.css("border-color",relationType.sireProp.backGroundColor);

                sentenceEle.append(relationLabelEle);
                relationLabelEle.attr("parentMentionId",parentMarkerId);




                //표시들이 중첩안되게 간격을 벌려준다.
                var labelTopOffset = 50;

                if (Math.abs(lastMarkerTop - parentMarkerEle.position().top) < 20){
                    //같은 줄인걸로 판정.
                    labelTopOffset = labelTopOffset + (relationLabelStackCount * 30) ;
                    relationLabelStackCount ++;
                } else {
                    //다른줄이 시작됐다면.
                    relationLabelStackCount = 1;
                    lineIndex++;
                };




                lastMarkerTop = parentMarkerEle.position().top;

                relationLabelEle.css("top",parentMarkerEle.position().top - labelTopOffset);

                var parentLeft = parentMarkerEle.position().left;
                var childLeft = childMarkerEle.position().left;
                var left =  (parentLeft < childLeft) ? parentLeft : childLeft;

                relationLabelEle.css("left",Math.abs(parentLeft - childLeft)/2 + left );

                var lableInDirection = null;
                var lableOutDirection = null;
                if (parentLeft <childLeft) {
                    lableInDirection = "Left";
                    lableOutDirection = "Right";
                } else {
                    lableInDirection = "Right";
                    lableOutDirection = "Left";
                };



                if (lineMarginGroupInfo[lineIndex]){
                    //자기보다 아래쪽에 있는 relationLabel 은 신경쓰지 않아도 된다.
                    //이문제인데....
                    lineMarginGroupInfo[lineIndex].relationLabels.push(relationLabelEle);
                } else {

                    var gtcToken = sentenceEle.find('span[mentionId="'+parentMarkerId+'"]');

                    lineMarginGroupInfo[lineIndex] = {"paddingEle":marginEle , "relationLabels":[]};
                    lineMarginGroupInfo[lineIndex].relationLabels.push(relationLabelEle);
                };



                jsPlumb.setContainer($("body"));

                jsPlumb.connect({ source:parentMarkerEle,
                    target:relationLabelEle,
                    anchors:[ "Top",lableInDirection ],
                    paintStyle:{ strokeWidth:1, stroke:"rgb(131,8,135)" },
                    endpoint:["Dot", { radius:1 }],
                    connector:["Bezier" , {curviness:90}],
                    overlays:[
                        ["Arrow" , { width:5, length:5, location:0.9 }]
                    ]
                });
                //connector:["Flowchart" , {cornerRadius:10}]

                jsPlumb.connect({ source:relationLabelEle,
                    target:childMarkerEle,
                    anchors:[ lableOutDirection,"Top" ],
                    paintStyle:{ strokeWidth:1, stroke:"rgb(131,8,135)" },
                    endpoint:["Dot", { radius:1 }],
                    connector:["Bezier" , {curviness:90}],
                    overlays:[
                        ["Arrow" , { width:5, length:5, location:0.9 }]
                    ]
                });


            };



        });
        recalcRelationAreaPadding1(lineMarginGroupInfo);


    };



    _p.processTokenEntityTypeMarkerSelection = function(markerEle){
        var entityTypeLabel = markerEle.attr("entityTypeLabel");
        var parentEntityType = _p.loadedEntityTypesLabelMap[entityTypeLabel];
        var parentRelations = $.map(_p.loadedRelationTypesIdMap, function(e){
            if (e.srcEntType == parentEntityType.id) {
                return e;
            }
        });
        _p.resetRelationTypeList(parentRelations);
        var childEntityTypeIdMap = {};

        for (var k in parentRelations){
            var relationType = parentRelations[k];
            if (!(relationType.tgtEntType in childEntityTypeIdMap)){
                childEntityTypeIdMap[relationType.tgtEntType] = 1;

            }
        };

        //일단 전부 불투명하게 해둔다.
        $("#document-holder").find(".tokenEntityTypeMarker , .relationLabel").each(function(index,ele){
            var ele = $(ele);
            ele.css("opacity","0.2");
        });

        $("#relationLineDrawingArea").find(".jsSimpleConnect").each(function(index,ele){
            var ele = $(ele);
            ele.css("opacity","0.2");
        });

        var sentenceEle = markerEle.closest(".gtcSentence");

        sentenceEle.find(".tokenEntityTypeMarker").each(function(index,childMarkerEle){
            var childMarkerEle = $(childMarkerEle);
            var entityTypeLabel = childMarkerEle.attr("entityTypeLabel");
            var childEntityType = _p.loadedEntityTypesLabelMap[entityTypeLabel];
            if (childEntityType.id in childEntityTypeIdMap){
                if (!childMarkerEle.is(markerEle)){
                    childMarkerEle.css("opacity","1");
                    childMarkerEle.addClass("relationTarget");
                };
            } else {
                childMarkerEle.css("opacity","0.2");
            };
        });


    _p.processSelectRelation = function(relationInfo){

        var parentEntityTypeLabel = relationInfo.parent.attr("entityTypeLabel");
        var childEntityTypeLabel = relationInfo.child.attr("entityTypeLabel");

        var parentEntityTypeId = _p.loadedEntityTypesLabelMap[parentEntityTypeLabel].id;
        var childEntityTypeId = _p.loadedEntityTypesLabelMap[childEntityTypeLabel].id;


        var validRelations = $.map(_p.loadedRelationTypesIdMap, function(e){
            if (e.srcEntType == parentEntityTypeId && e.tgtEntType == childEntityTypeId) {
                return e;
            }
        });

        _p.resetRelationTypeList(validRelations);

    }

    _p.processRelationCreation = function(relationInfo,selectedRelationTypeEle){
        var parentMentionId = relationInfo.parent.attr("mentionId");
        var childMentionId = relationInfo.child.attr("mentionId");
        var relationLabel = selectedRelationTypeEle.attr("gtcRelationLabel");

        var sentenceEle = $(relationInfo.parent.closest(".gtcSentence"));
        var sentenceId = sentenceEle.attr("sentenceId");
        var newRelationId = getNextRelationId();
        var newRelation = {
            "id" : sentenceId+"-r"+getNextRelationId(),
            "properties" : { },
            "type" : relationLabel,
            "args" : [ parentMentionId, childMentionId ]
        };


        var previousRelations = $.map(_p.loadedGroundTruth.relations, function(e){
            if (e.type == relationLabel && e.args[0] == parentMentionId && e.args[1] == childMentionId) {
                return e;
            }
        });
        if (previousRelations.length < 1){
            _p.loadedGroundTruth.relations.push(newRelation);
        };



    }

    function getNextRelationId(){
        var relations = _p.loadedGroundTruth.relations;
        var maxId = 0;
        for (var k in relations){
            var relation = relations[k];
            var id = relation.id.split("-")[1].replace("r","");
            id = id *1;
            if (id > maxId) {
                maxId = id;
            }
        }
        return maxId + 1;
    };


    };

	return module;
}($J1 || {}));