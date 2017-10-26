var attachCnt = 0;

$(document).ready(function()  {

	$(".contentsWrap .mainVisualDiv .tit1").fadeIn(3000);

	$(".contentsWrap .contents .leftDiv").css("height", $(".contentsWrap").height());

	$(".dim").click(function()  {
		popClose();
	});

	$(".dim3").click(function()  {
		popSlide("popup");
	});

	$(".dim2").click(function()  {
		popClose2();
	});

	$(".popup a.popClose").click(function()  {
		popClose();
	});

	$(".popup a.popClose2").click(function()  {
		popClose2();
	});
	$(".popup a.popClose3").click(function()  {
		popSlide("popup");
	});

	$(".popup .changeBtn").click(function()  {
		if ($(this).hasClass("on") == true)  {
			$(this).removeClass("on");
		}
		else  {
			$(this).addClass("on");
		}

		$(".popup .changeDiv").toggle();
	});

	$("header .dropdown .btn.dropdown-toggle.selectbox").click(function()  {
		if ($("header .dropdown").hasClass("open") == true)  {
			$("header .rightMenu li .dropdown .dropdown-menu").slideUp(500);
		}
		else  {
			$("header .rightMenu li .dropdown .dropdown-menu").slideDown(500);
		}
	});
});


function fileAppend(fName)  {
	attachCnt = attachCnt + 1;
	$(".contentsWrap .contents .contentsDiv .communityWriteDiv .contentsArea .attachArea .attachList").append("<li><a href=\"javascript:attachDel(\'attach" + attachCnt + "\');\" class='attach" + attachCnt + "'>" + fName + "</a></li>");
}

function attachDel(attachNo)  {
	$(".contentsWrap .contents .contentsDiv .communityWriteDiv .contentsArea .attachArea .attachList li ." + attachNo).parent().remove();
	attachCnt = attachCnt - 1;

}

function popSlide(popName)  {
	$(".dim3").css("width", $(".wrapDiv").width());
	$(".dim3").css("height", $(".wrapDiv").height());

	if ($(".popup.myInfo1").css("display") == "block")  {
		$(".dim3").hide();
		$(".popup." + popName).css("left", ($("header.sub .rightMenu li:first-child").offset().left - 130)); 
		$(".popup." + popName).slideUp(500);
	}
	else  {
		$(".dim3").show();
		$(".popup." + popName).css("left", ($("header.sub .rightMenu li:first-child").offset().left - 130)); 
		$(".popup." + popName).slideDown(500);

	}
	$(".popup a.popClose3").slideToggle(500);
};

function popOpen(popName)  {
	$(".dim").css("width", $(".wrapDiv").width());
	$(".dim").css("height", $(".wrapDiv").height());
	$(".dim").show();

	$(".popup." + popName).css("top", "calc(50% - (" + $(".popup." + popName).height() + "px / 2))"); 
	$(".popup." + popName).css("left", "calc(50% - (" + $(".popup." + popName).width() + "px / 2))"); 
	$(".popup." + popName).show();

	$(window).resize(function()  {
		window.resizeEvt;

		$(".dim").css("width", $(".wrapDiv").width());
		$(".dim").css("height", $(".wrapDiv").height());

		$(window).resize(function()  {
			clearTimeout(window.resizeEvt);

			$(".dim").css("width", $(".wrapDiv").width());
			$(".dim").css("height", $(".wrapDiv").height());
		});
	});
}

function popOpen2(popName)  {
	$(".dim2").css("width", $(".wrapDiv").width());
	$(".dim2").css("height", $(".wrapDiv").height());
	$(".dim2").show();

	$(".popup." + popName).css("top", "calc(50% - (" + $(".popup." + popName).height() + "px / 2))"); 
	$(".popup." + popName).css("left", "calc(50% - (" + $(".popup." + popName).width() + "px / 2))"); 
	$(".popup." + popName).show();

	$(window).resize(function()  {
		window.resizeEvt;

		$(".dim2").css("width", $(".wrapDiv").width());
		$(".dim2").css("height", $(".wrapDiv").height());

		$(window).resize(function()  {
			clearTimeout(window.resizeEvt);

			$(".dim2").css("width", $(".wrapDiv").width());
			$(".dim2").css("height", $(".wrapDiv").height());
		});
	});
}

function popClose()  {
	$(".dim").hide();
	$(".popup").hide();
}

function popClose2()  {
	$(".dim2").hide();
	$(".popup.msg").hide();
}