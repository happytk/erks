var $J1 = (function (module){
	var _p = module._p = module._p || {};

    _p.drawEntityRelations = function(relations){


        for (var k in relations){

            var relation = relations[k];

            var srcTgtRelationId = relation.srcEntType + "-" + relation.tgtEntType;
            var srcTgtRelation = _p.loadedSrcTgtRelationMap[srcTgtRelationId];
             //= {"shown":false,"connection":null,"relation":relationType};
//_p.loadedSrcTgtRelationMap[srcTgtRelationId];
//이걸 잘못만들었네. 안에 있는 relaton 이 배열이 들어가야하는데 딸랑 한개씩만 있음.

            _p.drawRelation(srcTgtRelation);

        };
    };

    _p.drawRelation = function(srcTgtRelation){
        if (!srcTgtRelation.shown){
            jsPlumb.setContainer("innerMap");

            var sourceEle = $("#"+srcTgtRelation.srcEntType);
            var targetEle = $("#"+srcTgtRelation.tgtEntType);

            if (!sourceEle.is(":visible")) {
                sourceEle.css("display","");
            };
            if (!targetEle.is(":visible")) {
                targetEle.css("display","");
            };

            var labels = "";
            for (var k in srcTgtRelation.relations){
                var relation = srcTgtRelation.relations[k];
                var label = relation.label;
                if ($J1._p.currentTypeSystemMode == "L" && relation.logical_value) {
                    label = relation.logical_value;
                };
                labels += label + " / ";
                if (((k+1) % 3) == 0){
                    labels +="<br>"
                };
            };
            labels = labels.slice(0,-1);

            var connection = jsPlumb.connect({
                source:sourceEle,
                target:targetEle,
                anchor:"Continuous",
                paintStyle:{ strokeWidth:1, stroke:"rgb(131,8,135)" },
                endpoint:["Dot", { radius:1 }],
                connector:["Bezier" , {curviness:90}],
                overlays:[
                    ["Arrow" , { width:5, length:5, location:0.9 }],
                     [ "Label", {label:labels, id:srcTgtRelation.relations[0].id}]
                ]
            });

//            connection.unbind("dblclick","**");


            connection.bind("dblclick",function(conn){
                var sourceId = _p.loadedRelationTypesIdMap[conn.id].srcEntType;
	            var targetId = _p.loadedRelationTypesIdMap[conn.id].tgtEntType;
               _p.resetRelationTypeDtl(sourceId,targetId)
            });

            jsPlumb.revalidate(srcTgtRelation.srcEntType);
            jsPlumb.revalidate(srcTgtRelation.tgtEntType);
            srcTgtRelation.shown = true;
            srcTgtRelation.connection = connection;
        }



    };

    _p.removeEntityRelations = function(relations){
        for (var k in relations){
            var relation = relations[k];
            var srcTgtRelationId = relation.srcEntType + "-" + relation.tgtEntType;
            var srcTgtRelation = _p.loadedSrcTgtRelationMap[srcTgtRelationId];
            _p.removeRelation(srcTgtRelation);
        };
    };

    _p.removeRelation = function(srcTgtRelation){
        if (srcTgtRelation.shown){
            //jsPlumb.detach(srcTgtRelation.connection);
            jsPlumb.deleteConnection(srcTgtRelation.connection);
            srcTgtRelation.shown = false;
            srcTgtRelation.connection = null;
        };
    };





	return module;
}($J1 || {}));