var $J1 = (function (module){
	var _p = module._p = module._p || {};

    var minimapScale = 1;
    var miniMapEle = $('#miniMap');
    var viewPointEle = $("#viewPoint");
    var diagramViewEle = $("#diagramView");

    function reCalcMinimapScale(){
        //var mapwidth = _p.innerMapEle.width();
        //var mapheight =  _p.innerMapEle.height();
        var mapwidth = 0;
        var mapheight = 0;

        _p.innerMapEle.find(".entity").each(function(index,ele){
            ele = $(ele);
            var maxWidth = ele.position().left + ele.width();
            if (maxWidth > mapwidth) {
                mapwidth = maxWidth;
            };
            var maxHeight = ele.position().top + ele.height();
            if (maxHeight > mapheight) {
                mapheight = maxHeight;
            };
        });
        var minimapwidth = miniMapEle.width();
        var minimapheight = miniMapEle.height();
        var Hscale = minimapwidth / mapwidth;
        var Vscale = minimapheight / mapheight;
        minimapScale = (Hscale < Vscale) ? Hscale : Vscale;
    };


    _p.resetMiniMap = function(){
        reCalcMinimapScale();
        try {
            $("#viewPoint").draggable("destroy");
        } catch (err){

        }
        viewPointEle.draggable({
            containment: "parent"
        });
        miniMapEle.unbind("click");
        miniMapEle.on("click",function(e){
            e.stopPropagation();
            var x = e.pageX-$(this).offset().left;
            var y = e.pageY-$(this).offset().top;
            var viewPointX = viewPointEle.position().left;
            var viewPointWidth = viewPointEle.width()
            var viewPointY = viewPointEle.position().top;
            var viewPointHeight = viewPointEle.height();
            if (x > viewPointX && x < viewPointX + viewPointWidth && y >viewPointY && y < viewPointY+viewPointHeight){

            } else {
                x = x-(viewPointWidth/2);
                y = y-(viewPointHeight/2);
                if (x<0) {
                    x=0;
                }
                if (y<0) {
                    y=0;
                }
                viewPointEle.animate({"left":x,"top":y},0);
            }

            _p.innerMapEle.css("top",-1*y/minimapScale);
            _p.innerMapEle.css("left",-1*x/minimapScale);


        });

        miniMapEle.children().remove('.minimapEntity');

        _p.innerMapEle.find(".entity").each(function(index,ele){
            ele = $(ele);
            if (ele.is(":visible")) {
                var entId = _p.getObjectId(ele);
                var miniEleId = "mini_"+entId;
                $('<div id="'+miniEleId+'" class="minimapEntity"></div>')
                .width(ele.width()*minimapScale)
                .height(ele.height()*minimapScale)
                .css("left",ele.position().left*minimapScale)
                .css("top",ele.position().top*minimapScale)
                .css("background",ele.children(".typeColorLine").css("background-color"))
                .css("position","absolute")
                .appendTo(miniMapEle);


            }
        });
        _p.drawViewPoint();
    };

    _p.resetMiniMapEnt = function(entId){
        var entEle = $("#"+entId);
        if (entEle.length > 0){
            $('#mini_'+entId).remove();
            var miniEleId = "mini_"+entId;
            $('<div id="'+miniEleId+'" class="minimapEntity"></div>')
            .width(entEle.width()*minimapScale)
            .height(entEle.height()*minimapScale)
            .css("left",entEle.position().left*minimapScale)
            .css("top",entEle.position().top*minimapScale)
            .css("background",entEle.children(".typeColorLine").css("background-color"))
            .css("position","absolute")
            .appendTo(miniMapEle);
        } else {
            $('#mini_'+entId).remove();
        }

    };


    _p.drawViewPoint = function(){
        _p.resetMinimapViewpoint();
        viewPointEle.unbind('drag');
        viewPointEle.bind('drag',$.proxy(function( event ){
                _p.innerMapEle.css("top",-1*this.position().top/minimapScale);
                _p.innerMapEle.css("left",-1*this.position().left/minimapScale);
            },viewPointEle));
    }

    _p.resetMinimapViewpoint = function(){
        reCalcMinimapScale();
        var left = _p.innerMapEle.position().left*minimapScale*(-1);
        if (left < 0 ) {
            left = 0;
        };
        var top = _p.innerMapEle.position().top*minimapScale*(-1)
        if (top < 0 ) {
            top = 0;
        };

        viewPointEle
            .width($('#diagramView').width()*minimapScale)
            .height($('#diagramView').height()*minimapScale)
            .css("left",left)
            .css("top",top);


    };



	return module;
}($J1 || {}));

