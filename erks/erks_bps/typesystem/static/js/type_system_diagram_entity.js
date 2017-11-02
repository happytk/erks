var $J1 = (function (module){
	var _p = module._p = module._p || {};


    var diagramViewEle = $("#diagramView");


    _p.getOutgoingRelationCount = function(entId){
        var outgoingRelationMap = $J1._p.loadedEntitySrcRelationIdMap[entId];
        var outgoingRelationCount = 0;
        if (outgoingRelationMap) {
            outgoingRelationCount = outgoingRelationMap.relations.length;
        };
        return outgoingRelationCount;
    };

    _p.getIncomingRelationCount = function(entId){
        var incomingRelationMap = $J1._p.loadedEntityTgtRelationIdMap[entId];
        var incomingRelationCount = 0;
        if (incomingRelationMap) {
            incomingRelationCount = incomingRelationMap.relations.length;
        };
        return incomingRelationCount;
    };





    _p.selectEntity = function(ele){
        if (_p.SelectedEntity) {
            _p.unselectEntity(_p.SelectedEntity);
        }
        ele.addClass("thickBox");
        _p.SelectedEntity = ele;
    };

    _p.unselectEntity = function(ele){
        if (!ele) {
            return;
        };
        try{
            ele.removeClass("thickBox");
            //ele.entity("removeResizable");
            //_p.disableEntityAttrSort(ele);
            _p.SelectedEntity = null;
        } catch (err){

        }
    };




    _p.resetTypeSystemDiagram = function(){
        jsPlumb.deleteEveryConnection();
        jsPlumb.deleteEveryEndpoint();
        _p.innerMapEle.empty();
        jsPlumb.setContainer("innerMap");

        var Xoffset = 0;
        var Yoffset = 0;

        for (var k in _p.loadedEntityTypesLabelMap){
            var entityType = _p.loadedEntityTypesLabelMap[k];

            var diagramItem = _p.loadedTypeSystemDiagram[k];

            drawTypeSystem(entityType, diagramItem, Xoffset*120, Yoffset*120);


            if (!diagramItem) {
                Xoffset++;
                if (Xoffset>10){
                    Xoffset = 0;
                    Yoffset++;
                }
            };
        };


    };


    function drawTypeSystem(entityType, diagramItem, Xoffset, Yoffset){

        if (!diagramItem){
            diagramItem = {};
            diagramItem.x = Xoffset;
            diagramItem.y = Yoffset;
            //없으면 만들어둔다. 나중에 저장할때 모든 typeSystem에 대한 diagram항목이 만들어질것임.
            _p.loadedTypeSystemDiagram[entityType.label] = diagramItem;
        };
        var roles = [];
        for (var k in entityType.sireProp.roles){
            var roleId = entityType.sireProp.roles[k];
            var roleObject = {"id":roleId, "label":_p.loadedEntityTypesIdMap[roleId].label};
            roles.push(roleObject);
        };

        var entity = {
            "id":entityType.id,
            "label":entityType.label
        }

        $('<div></div>').entity(entity).entity("resetDraggable").entity("setShowOutgoing").entity("setShowIncoming").appendTo(_p.innerMapEle);

    };

    _p.showTypeSystemEntity = function(entId){
        var entEle = $("#"+entId);
        entEle.css("display","");
    };

    _p.hideTypeSystemEntity = function(entId){
        var entEle = $("#"+entId);
        entEle.css("display","None");
    };

    _p.processEntityDelete = function(entId){

        var entDtl = _p.loadedEntityTypesIdMap[entId];
        var entLabel = entDtl.label;

        if (_p.loadedEntitySrcRelationIdMap[entId]){
            for (var k in _p.loadedEntitySrcRelationIdMap[entId].relations){
                try{
                    var relId = _p.loadedEntitySrcRelationIdMap[entId].relations[k].id;
                    var relLabel = _p.loadedEntitySrcRelationIdMap[entId].relations[k].label;
                    delete _p.loadedRelationTypesIdMap[relId];
                    delete _p.loadedRelationTypesLabelMap[relLabel];
                } catch (ex){
                }
            };
        }

        if (_p.loadedEntityTgtRelationIdMap[entId]){
            for (var k in _p.loadedEntityTgtRelationIdMap[entId].relations){
                try{
                    var relId = _p.loadedEntityTgtRelationIdMap[entId].relations[k].id;
                    var relLabel = _p.loadedEntityTgtRelationIdMap[entId].relations[k].label;
                    delete _p.loadedRelationTypesIdMap[relId];
                    delete _p.loadedRelationTypesLabelMap[relLabel];
                } catch (ex){
                }
            };
        }

        for (var k in _p.loadedEntityTypesIdMap){
            var rolesList = _p.loadedEntityTypesIdMap[k].sireProp.roles;
            newRolesList = $.grep(rolesList, function(value) {
              return value != entId;
            });
            _p.loadedEntityTypesIdMap[k].sireProp.roles = newRolesList;


        }


        delete _p.loadedEntityTypesLabelMap[entLabel];
        delete _p.loadedEntityTypesIdMap[entId];
        delete _p.loadedTypeSystemDiagram[entLabel];

        _p.resetRelationMaps();
        _p.innerMapEle.empty();
        _p.resetTypeSystemDiagram();
        _p.resetMiniMap();

    }




	return module;
}($J1 || {}));