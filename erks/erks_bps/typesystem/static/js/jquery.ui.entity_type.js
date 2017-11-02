/*!
 * jQuery UI Entity 1.0
 *
 * Copyright 2012, Copyright 2012, Jiwon,Cha (chazzy1@gmail.com)
 * Dual licensed under the MIT or GPL Version 2 licenses.
 * http://jquery.org/license
 *
 * http://...
 *
 * Depends:
 *	
 */
 
 /*
	entity 생성시 인자
	{id: , x:, y:, width:, height:, entTyp:, entNm:, tabNm:, Pattr:[{PKYN:, colNm:, dataTyp:, nullYN:, FKYN:}, ], Lattr:[{PKYN:, attrNm:, FKYN: }]}
	entTyp:A(모두), P(PhysicalOnly),L(LogicalOnly)
	
	
 
 
 
 
 */
(function( $, undefined ) {


$.widget( "ui.entity", {

    options: {
        id:"",
        label:"",
    },


    _create: function() {
		this._drawEntity();
		
    },
    
    drawVirtual: function() {
    	this.element.empty();
    	this.element.resizable();
    },
    disableDraggable: function(){
        this.element.unbind('dragstart');
        this.element.unbind('drag');
        this.element.unbind('dragstop');
        try{
            this.element.draggable( "destroy" );
        } catch (ex){

        };

    },
    resetDraggable: function(){
    	this.element.draggable({
			stack: ".objectContainer",
			cursor:"move",
			containment: "parent"
		});
		this.element.css('position',"absolute");//IE때문임
		this.element.unbind('dragstart');
		this.element.bind('dragstart',$.proxy(function( event ){
		/*
            $J1._p.refreshEmbededObjectList(this.options.id);
		    var maxZindex = $J1._p.getMaxEntZ();
            $J1._p.setZIndexForEmbededObject(this.options.id,maxZindex);
            $J1._p.embededIdTmpList = [];
            $J1._p.createEmbededIdList(this.options.id);
            */
        },this));
		this.element.unbind('drag');
		this.element.bind('drag',$.proxy(function( event ){
		        var entId = $J1._p.getObjectId(this.element);
                if (this.element.hasClass('jtk-endpoint-anchor')){


                    jsPlumb.revalidate(entId);
                };
                $J1._p.resetMiniMapEnt(entId);

		/*
			try{
			    var entId = this.options.id;
			    var entDtl = $J1._p.loadedEntDtl[entId];
				if ("relations" in entDtl && entDtl.relations["count"] <4){
					this.refreshRelation();
				};
				$J1._p.refreshEmbededObjectRelations(entId);
			} catch (err){
				//this.refreshRelation();
			};
			try{
				this.refreshBookmarks();
			} catch (err){

			}
			*/
        },this));
		this.element.unbind('dragstop');
		this.element.bind('dragstop',$.proxy(function( event ){
		    var label = this.options.label;
		    $J1._p.loadedTypeSystemDiagram[label].x =this.element.position().left;
		    $J1._p.loadedTypeSystemDiagram[label].y =this.element.position().top;
            $J1._p.resetMiniMapEnt($J1._p.getObjectId(this.element));

        },this));

    },
    setShowOutgoing: function(){
        var ele = this.element.find(".relationToggleOutgoing");
        ele.addClass("toggleShow");
        ele.removeClass("toggleHide");
        ele.html('Show Outgoing '+$J1._p.getOutgoingRelationCount(this.options.id)+' <span class="glyphicon glyphicon-arrow-right" aria-hidden="true">');
    },
    setHideOutgoing: function(){
        var ele = this.element.find(".relationToggleOutgoing");
        ele.removeClass("toggleShow");
        ele.addClass("toggleHide");
        ele.html('Hide Outgoing '+$J1._p.getOutgoingRelationCount(this.options.id)+' <span class="glyphicon glyphicon-arrow-right" aria-hidden="true">');
    },
    setShowIncoming: function(){
        var ele = this.element.find(".relationToggleIncoming");
        ele.addClass("toggleShow");
        ele.removeClass("toggleHide");
        ele.html('Show Incoming '+$J1._p.getIncomingRelationCount(this.options.id)+' <span class="glyphicon glyphicon-arrow-left" aria-hidden="true">');
    },
    setHideIncoming: function(){
        var ele = this.element.find(".relationToggleIncoming");
        ele.removeClass("toggleShow");
        ele.addClass("toggleHide");
        ele.html('Hide Incoming '+$J1._p.getIncomingRelationCount(this.options.id)+' <span class="glyphicon glyphicon-arrow-left" aria-hidden="true">');
    },

	_drawEntity: function() {
		this.element.attr("id",this.options.id);
		this.element.addClass("objectContainer");
        //this.resetDraggable();
        this.resetContents();

	},
	resetContents: function() {
		this.options.isMinimalMode = false;
		this.element.empty();
        var label = this.options.label;

		var entityType = $J1._p.loadedEntityTypesLabelMap[label];
		var diagramItem = $J1._p.loadedTypeSystemDiagram[label];

		this.element.css("top" , diagramItem.y);
		this.element.css("left" , diagramItem.x);

        this.element.addClass("entity");
        this.element.addClass("entityOuter");

        var labelArea = $('<div class="labelArea"></div>');


        if ($J1._p.currentTypeSystemMode == "L" && entityType.logical_value) {
            label = entityType.logical_value;
        };


        labelArea.html(label);
        this.element.append(labelArea);

        var typeColorLine = $('<div style="background-color:'+entityType.sireProp.backGroundColor+'" class="typeColorLine">');
        this.element.append(typeColorLine);


        var rolesContainer = $('<div style="border-color:'+entityType.sireProp.backGroundColor+'" class="attributeContainer">');

        var relationContainer = $('<div style="border-color:'+entityType.sireProp.backGroundColor+'" class="attributeContainer">');

        var outgoingRelationCount = $J1._p.getOutgoingRelationCount(this.options.id);
        var incomingRelationCount = $J1._p.getIncomingRelationCount(this.options.id);

        var totalCount = outgoingRelationCount+incomingRelationCount;
        var relationCountEle = $('<div class="attributeTitle">Relations: '+totalCount+'</div>');
        relationContainer.append(relationCountEle);


        if (outgoingRelationCount){
            var showOutgoingEle = $('<div class="relationToggleOutgoing"></div>');
            relationContainer.append(showOutgoingEle);
        };



        if (incomingRelationCount){
            var showIncomingEle = $('<div class="relationToggleIncoming"></div>');
            relationContainer.append(showIncomingEle);
        };

        this.element.append(relationContainer);

        var rolesAreaTitleEle = $('<div class="attributeTitle">Roles:</div>');
        rolesContainer.append(rolesAreaTitleEle);
        var loopCount = 0;
        for (var k in entityType.sireProp.roles){
            var roleId = entityType.sireProp.roles[k];
            var roleEle = $('<div class="attributeItem"></div>');
            var roleEnt = $J1._p.loadedEntityTypesIdMap[roleId];
            var label = roleEnt.label;
            if ($J1._p.currentTypeSystemMode == "L" && roleEnt.logical_value) {
                label = roleEnt.logical_value;
            };
            roleEle.html(label);
            rolesContainer.append(roleEle);
            loopCount ++;
            if (loopCount > 6){
                rolesContainer.append($('<div>...</div>'));
                break;
            }
        };
        this.element.append(rolesContainer);


        var subtypeContainer = $('<div style="border-color:'+entityType.sireProp.backGroundColor+'" class="attributeContainer">');
        var subtypeAreaTitleEle = $('<div class="attributeTitle">Subtypes:</div>');
        subtypeContainer.append(subtypeAreaTitleEle);
        for (var k in entityType.sireProp.subtypes){
            var roleEle = $('<div class="attributeItem"></div>');
            roleEle.html(entityType.sireProp.subtypes[k]);
            subtypeContainer.append(roleEle);
        };
        this.element.append(subtypeContainer);


        this.element.show();


        return;

	},	

	changeId: function(newId){
		this.options.id = newId;
		this.element.attr("id",newId);
	},	


    // Use the _setOption method to respond to changes to options

    _setOption: function( key, value ) {
      switch( key ) {

        case "clear":
          // handle changes to clear option

          break;

      }

      // In jQuery UI 1.8, you have to manually invoke the _setOption method from the base widget

      $.Widget.prototype._setOption.apply( this, arguments );
      // In jQuery UI 1.9 and above, you use the _super method instead
      //this._super( "_setOption", key, value );

    },
 
    // Use the destroy method to clean up any modifications your widget has made to the DOM

    destroy: function() {

      // In jQuery UI 1.8, you must invoke the destroy method from the base widget

      $.Widget.prototype.destroy.call( this );
      // In jQuery UI 1.9 and above, you would define _destroy instead of destroy and not call the base method

    }

  });


})(jQuery);
