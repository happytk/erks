
var $J1 = (function (module){
	var _p = module._p = module._p || {};

    _p.processMentionToolUIReset = function(){
        $("#relationToolRightSideBar").css("display","none");
        $("#mentionToolRightSideBar").css("display","");
        activateMentionToolDocumentUI();
        _p.clearRelationDrawingArea();
        _p.resetMentionDisplay();
    };

    function activateMentionToolDocumentUI(){
        _p.currentToolMode = _p.toolModeEnum.mentionTool;
        $("#document-holder").find(".gtcTokenRelationMargin, .tokenEntityTypeMarker").remove();
        _p.clearMentionTargetSelection();
        _p.activeSelection = null;

    };

    _p.resetMentionTypeClass = function(){
        $("#list-mention-type").empty();
        for (var k in _p.loadedSireInfo.entityProp.mentionType) {
            mentionType = _p.loadedSireInfo.entityProp.mentionType[k];
            drawMentionType(mentionType);
        };
        $("#list-mention-class").empty();
        for (var k in _p.loadedSireInfo.entityProp.clazz) {
            mentionClass = _p.loadedSireInfo.entityProp.clazz[k];
            drawMentionClass(mentionClass);
        }

    };


    function drawMentionClass(item){
        var style = "background-color:" + item.backGroundColor + "; color:"+item.color;
        var item = $('<div><div class="itemMentionIcon" style="'+style+'">'+item.hotkey+'</div><div class="itemLabel">'+item.name+'</div></div>')
        $("#list-mention-class").append(item);
    };

    function drawMentionType(item){
        var style = "background-color:" + item.backGroundColor + "; color:"+item.color;
        var item = $('<div><div class="itemMentionIcon" style="'+style+'">'+item.hotkey+'</div><div class="itemLabel">'+item.name+'</div></div>')
        $("#list-mention-type").append(item);
    };

    function drawEntityTypeItem(item){
        var label = item.label;
        if (_p.currentTypeSystemMode == "L" && item.logical_value) {
            label = item.logical_value;
        };
        var style = "background-color:" + item.sireProp.backGroundColor + "; color:"+item.sireProp.color;
        var item = $('<div gtcMentionLabel="'+item.label+'" id="'+item.id+'" class="gtcEntityType"><div class="itemMentionIcon" style="'+style+'">'+item.sireProp.hotkey+'</div><div class="itemLabel">'+label+'</div></div>');


        $("#list-entity-type").append(item);

        //이거 왜 안되나 모르겠음.
        //item.attr("gtcMentionLabel",item.label);
    };

    _p.drawSentence = function(sentence,index){
        var sentenceId = "gtcSentence-" + sentence.id;
        var sentenceEle = $('<div id="'+sentenceId+'" class="gtcSentence"></div>');
        var sentenceIndexEle = $('<div class="sentenceNumber">'+index+'</div>');
        sentenceEle.append(sentenceIndexEle);
        sentenceEle.attr("sentenceId",sentence.id);
        $("#document-holder").append(sentenceEle);
        for (var k=0; k<sentence.tokens.length; k++){
            var token = sentence.tokens[k];
            drawToken(sentenceEle,token);
            if (k+1 <= sentence.tokens.length) {
                drawBlank(sentenceEle,token,sentence.tokens[k+1]);
            }
        }
    };

    function drawToken(sentenceEle,token){
        var tokenId = "gtcToken-"+token.id;
        var tokenEle = $('<span id="'+tokenId+'" class="gtcToken" ></span>');
        var tokenTextEle = $('<span class="gtcTokenText">'+token.text+'</span>')

        var tokenSelectionEle = $('<span style="display:none" class="gtcTokenSelection"></span>')

        tokenEle.append(tokenTextEle);
        tokenEle.append(tokenSelectionEle);
        tokenEle.append("<wbr>");

        sentenceEle.append(tokenEle);

        tokenSelectionEle.css("width",tokenTextEle.outerWidth()+2);
        tokenSelectionEle.css("height",tokenTextEle.height()+1);
        tokenSelectionEle.css("left","-1px");
        tokenSelectionEle.css("top","-2px");
    };

    function drawBlank(sentenceEle,token,nextToken){

        if (nextToken && nextToken.begin - token.end) {
            var tokenId = "gtcToken-ws-b"+token.end;
            var tokenEle = $('<span id="'+tokenId+'" class="gtcToken" ></span>');
            var tokenTextEle = $('<span class="gtcTokenText"> </span>')
            var tokenSelectionEle = $('<span style="display:none" class="gtcTokenSelection"></span>')

            tokenEle.append(tokenTextEle);
            tokenEle.append(tokenSelectionEle);

            sentenceEle.append(tokenEle);

            tokenSelectionEle.css("width",tokenTextEle.outerWidth()+7);
            tokenSelectionEle.css("height",tokenTextEle.height()+1);
            tokenSelectionEle.css("left","-1px");
            tokenSelectionEle.css("top","-2px");
        }
    };

    _p.resetEntityTypeList = function(){
        $("#list-entity-type").empty();
        for (var id in _p.loadedEntityTypesLabelMap){
            drawEntityTypeItem(_p.loadedEntityTypesLabelMap[id]);
        };
    };


    function getNextMentionId(){
        var mentions = _p.loadedGroundTruth.mentions;
        var maxId = 0;
        for (var k in mentions){
            var mention = mentions[k];
            var id = mention.id.split("-")[1].replace("m","");
            id = id *1;
            if (id > maxId) {
                maxId = id;
            }
        }
        return maxId + 1;
    };

    _p.processEntityTypeAssignment = function(ele){
        ele = $(ele);
        var entityType = _p.loadedEntityTypesLabelMap[ele.attr("gtcMentionLabel")]
        if (_p.activeSelection){


            var mentions = _p.loadedGroundTruth.mentions;
            var newMention = getBaseMentionObject();

            newMention.id = _p.activeSelection.sentenceId+"-"+"m"+getNextMentionId();

            var entityTypeLabel =entityType.label;

            newMention.type = entityTypeLabel;
            newMention.begin = _p.activeSelection.begin;
            newMention.end = _p.activeSelection.end;

            assignEntityType(newMention);

            mentions.push(newMention);
            _p.clearMentionTargetSelection();
            _p.activeSelection = null;

        }
    };

    //_p.activeSelection이 있을것을 요구한다. 최초로 로딩시 이미 있는 멘션 칠할때도 하나씩 activeSession 을 만들거 가면서 이작업을 한다.(drawMentionTargetSelection을 이용해 자동으로 됨)
    function assignEntityType(mention){
        var entityType = _p.loadedEntityTypesLabelMap[mention.type]
        for (var k in _p.activeSelection.tokens){
            var tokenEle = _p.activeSelection.tokens[k];
            tokenEle.addClass("entityTypeAssigned");
            tokenEle.attr("entityTypeLabel",mention.type);
            tokenEle.attr("mentionId",mention.id);
            tokenEle.css("background-color",entityType.sireProp.backGroundColor);
            tokenEle.css("color",entityType.sireProp.color);
        };
    };

    _p.resetMentionDisplay = function(){
        var mentions = _p.loadedGroundTruth.mentions;
        for (var k in mentions){
            var mention = mentions[k];

            var sentenceId = mention.id.split("-")[0]
            _p.activeSelection= {"sentenceId":sentenceId, "id":mention.id, "begin":mention.begin, "end":mention.end, "tokens":{}};
            _p.drawMentionTargetSelection(sentenceId,mention.begin,mention.end);
            assignEntityType(mention);

        };
        _p.clearMentionTargetSelection();
        _p.activeSelection = null;
    };

    _p.processTokenSelection = function(tokenEle){
        var tokenEleId = _p.getObjectId(tokenEle);
        //gtcToken-s0-t3

        var sentenceId = tokenEleId.split("-")[1];
        var tokenId = tokenEleId.split("-")[1]+"-"+tokenEleId.split("-")[2];
        var sentence = $.grep(_p.loadedGroundTruth.sentences, function(e){ return e.id == sentenceId; })[0];

        if (sentence) {

            if (tokenEle.hasClass("entityTypeAssigned")){
                var entityTypeLabel = tokenEle.attr("entityTypeLabel");
                var mention = $.grep(_p.loadedGroundTruth.mentions, function(e){ return e.type == entityTypeLabel; })[0];
                _p.clearMentionTargetSelection();
                _p.drawMentionTargetSelection(sentenceId,mention.begin,mention.end);



            } else {

                var token = $.grep(sentence.tokens, function(e){ return e.id == tokenId; })[0];








                if (_p.activeSelection && sentenceId == _p.activeSelection.sentenceId){

                    var minPoint = _p.activeSelection.begin;
                    var maxPoint = _p.activeSelection.end;

                    if (token.begin < minPoint ) {
                        minPoint = token.begin;
                    };

                    if (token.end > maxPoint ) {
                        maxPoint = token.end;
                    };
                    _p.activeSelection.begin = minPoint;
                    _p.activeSelection.end = maxPoint;



                    _p.clearMentionTargetSelection();
                    _p.drawMentionTargetSelection(sentenceId,minPoint,maxPoint);

                } else {

                    _p.clearMentionTargetSelection();
                    var mentionId = sentenceId + "-m0";
                    _p.activeSelection= {"sentenceId":sentenceId, "id":mentionId, "begin":token.begin, "end":token.end, "tokens":{}};
                    _p.drawMentionTargetSelection(sentenceId,token.begin,token.end);

                };
            }



        }

    };

    _p.clearMentionTargetSelection = function(){
        $("#document-holder").find(".gtcTokenSelection").each(function(index,ele){
            $(ele).removeClass("gtcTokenSelectionBegin");
            $(ele).removeClass("gtcTokenSelectionEnd");
            $(ele).css("display","none");
        });
    }




    _p.drawMentionTargetSelection = function(sentenceId,from,to){
        var sentence = _p.sentencesIdMap[sentenceId];

        for (var k in sentence.tokens){
            var token =  sentence.tokens[k];
            var tokenEle = $("#gtcToken-"+token.id);

            if (from >= token.begin && from <= token.end){
                var tokenTo = to;
                var endMark = true;
                if (tokenTo > token.end){
                    tokenTo = token.end;
                    endMark = false;
                };
                drawTokenSelection(tokenEle,from-token.begin,tokenTo-token.begin,true,endMark);
            } else if (from < token.begin && to > token.end) {
                //앞에 있는 공백까지 같이 막아줌.

                drawPreBlankSelection(tokenEle);

                drawTokenSelection(tokenEle,0,token.end-token.begin,false,false);
            } else if (from < token.begin && to >= token.begin && to <= token.end){
                var tokenFrom = from;
                var beginMark = true;
                tokenFrom = token.begin;
                //앞에 있는 공백까지 같이 막아줌.
                drawPreBlankSelection(tokenEle);
                drawTokenSelection(tokenEle,tokenFrom-token.begin,to-token.begin,false,true);
            }
        }

    }
    function drawPreBlankSelection(tokenEle){
        var blankEle = tokenEle.prev();
        var tokenEleId = _p.getObjectId(blankEle);
        if (_p.activeSelection) {
            _p.activeSelection.tokens[tokenEleId] = blankEle;
        }
        blankEle.find(".gtcTokenSelection").css("display","");
    }

    function drawTokenSelection(tokenEle,from, to, beginMark, endMark){
        var tokenEleId = _p.getObjectId(tokenEle);

        //선택된 토큰들을 한번에 칠해줄려고 이걸 하는데,
        //본 펑션이 나중에 이미 선택된 멘션을 클릭할때도 사용되므로, 그때는 아래의 작업을 안해야함. 그래서 체크한다.
        if (_p.activeSelection) {
            _p.activeSelection.tokens[tokenEleId] = tokenEle;
        };


        var range = document.createRange();
        var textToken = tokenEle.find(".gtcTokenText");
        var textNode = textToken[0].firstChild;
        range.setStart(textNode,from);
        range.setEnd(textNode,to);
        var rects = range.getClientRects()[0];
        var tokenSelectionEle = tokenEle.find(".gtcTokenSelection");

        tokenSelectionEle.css("display","");
        if (beginMark) {
            tokenSelectionEle.addClass("gtcTokenSelectionBegin");
        };
        if (endMark) {
            tokenSelectionEle.addClass("gtcTokenSelectionEnd");
        };

        var leftOffset = tokenEle.offset().left;

        tokenSelectionEle.css("left",rects.left-leftOffset);
        tokenSelectionEle.css("width",rects.width);


    };

    function getBaseMentionObject(){
        //entityTypeId 이거 내가 추가한 속성임.
        return {
            "id" : null,
            "properties" : {
              "SIRE_MENTION_ROLE" : "NONE",
              "SIRE_ENTITY_SUBTYPE" : "NONE",
              "SIRE_MENTION_TYPE" : "NONE",
              "SIRE_MENTION_CLASS" : "NONE"
            },
            "type" : null,
            "begin" : null,
            "end" : null,
            "inCoref" : false,
        }
    }

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