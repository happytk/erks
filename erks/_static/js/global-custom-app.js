
    // var gt;
    // var _ ;
    // var ngettext;

    // var init_gettext = function(){
    //     $.get(Flask.url_for('portal.locale'), function( data ) {
    //         gt = new Gettext({domain: data});
    //         _ = function(msgid) { return gt.gettext(msgid); };
    //         ngettext = function(msgid, msgid_plural, n) { return gt.ngettext(msgid, msgid_plural, n); };
    //     });
    // };

    // $(document).ready(function() {
    //     init_gettext();

    // });


$(document).ready(function() {

    /*
    App configuration
    */
    App.setAssetsPath('/comp/static/assets/');

    /*
    parsley configuration
    */

    Parsley.options.successClass = 'has-success';
    Parsley.options.errorClass = 'has-error';
    Parsley.options.classHandler = function (parsleyfield) {
        return parsleyfield.$element.closest('.form-group');
    };
    Parsley.options.errorsContainer = function (parsleyfield) {
        // console.log('helloworld');
        var $container = parsleyfield.$element.closest('.form-group').find(".help-block");
        // console.log($container);
        // console.log($container.length);
        if ($container.length === 0) {
            $container = $("<span class='help-block has-error'></span>").insertAfter(parsleyfield.$element);
        }
        $container.addClass('has-error');
        return $container;
    };
    Parsley.options.errorsWrapper = '<span></span>';
    Parsley.options.errorTemplate = '<span></span>';
    Parsley.on('field:error', function() {
      // This global callback will be called for any field that fails validation.
      console.log('Validation failed for: ', this.$element);
    });
    Parsley.on('form:error', function(parsley) {
      // This global callback will be called for any field that fails validation.
        // console.log('form validation error', parsley);
        App.alert({
            container: parsley.$element.closest('.portlet-body'),
            place: 'prepend', // append or prepent in container
            type: 'danger', // alert's type
            message: _("입력폼 중 확인이 필요한 부분이 있습니다."),  // alert's message
            close: true, // make alert closable
            reset: true, // close all previouse alerts first
            focus: true, // auto scroll to the alert after shown
            closeInSeconds: 5, // auto close after defined seconds
            icon: 'fa fa-check' // put icon class before the message
        });
    });
    Parsley.on('form:validated', function() {
        console.log('when validated');
    });
    Parsley.on('form:validate', function() {
        console.log('when validate');
    });
    Parsley.on('form:init', function() {
        console.log('when init');
    });
    Parsley.on('form:success', function() {
        console.log('when success');
    });

    /*
    portlet-form-configuration
    */
    //이 부분은 ajax-portlet-load후에 불려져야 의미있음
    var clean_ajax_clonable = function() {
        $('[data-toggle=fieldset-entry-clonable]').find(':input').each(function() {
            var elem_id = $(this).attr('id');
            var elem_num_source = parseInt(elem_id.replace(/.*-(\d{1,4})/m, '$1'));
            // console.log(elem_id, elem_num_source, 'xxxxx');
            //숫자일 경우에만 update
            if (!isNaN(elem_num_source)) {
                // console.log('NAN PASS?', elem_id, elem_num_source, 'xxxxx');
                var id = $(this).attr('id').replace('-'+(elem_num_source), '-[idx]');
                $(this).attr('name', id).attr('id', id);
                // console.log(id);
            }
        });
    };

    /* fieldset에 대한 공용처리logic */
    $('body').on('click', 'div[data-toggle=fieldset] button[data-toggle=fieldset-add-row]', function(e) {

        //clone하기전에 init한다.
        clean_ajax_clonable();

        var $form = $(this).closest('div[data-toggle=fieldset]');
        var target = $($(this).data("target"));
        // console.log(target);
        var oldrow = target.find("[data-toggle=fieldset-entry-clonable]:first");
        var row = oldrow.clone(true, true);
        // console.log(row.find(":input")[0]);
        row.toggleClass("hide");
        row.attr("data-toggle", "fieldset-entry");

        var elem_id = row.find(":input")[0].id;
        var elem_num_source = parseInt(elem_id.replace(/.*-(\d{1,4})/m, '$1'));
        var elem_num = $form.find("[data-toggle=fieldset-entry]").length;
        row.attr('data-id', elem_num);
        row.find(":input").each(function() {
            // console.log(this);
            var id = $(this).attr('id').replace('-[idx]', '-' + (elem_num));
            // var id = $(this).attr('id').replace('-' + (elem_num_source), '-' + (elem_num));
            $(this).attr('name', id).attr('id', id).val('').removeAttr("checked");
        });
        oldrow.after(row);
    });

    $('body').on('click', 'div[data-toggle=fieldset] button[data-toggle=fieldset-remove-row]', function(e) {
        var $form = $(this).closest('div[data-toggle=fieldset]');
        // if($form.find("[data-toggle=fieldset-entry]").length > 1) {
            var thisRow = $(this).closest("[data-toggle=fieldset-entry]");
            thisRow.remove();
        // }
    });

    /* daterange에 대한 공용처리logic */
    $('body').on('click', '.form-group .help-block > #btn_code_range_default_set', function(e) {

        e.preventDefault();
        var today_str = $.datepicker.formatDate('yymmdd', new Date());
        var f = $(this).closest('div.form-group');
        f.find('.date-picker input:first').val(today_str);
        f.find('.date-picker input:last').val('99991231');
    });

    /* portlet 내부의 form에 대해서는 기본적으로 parsley form */
    /* DONT UNCOMMENT THIS -- 이렇게 하고 싶었으나 필요하지 않은 부분에 대해서도 마구잡이로 form에 잡힌다. */
    // $('.portlet .portlet-body form').parsley();

    // $('body').on('click', '.portlet .portlet-body form > .form-actions .red', function(e) {
    $('body').on('submit', '.portlet .portlet-body form', function(e) {
        // alert('!!!');
        var $form = $(this);
        var $parsley = $form.parsley();
        var $el = $form.closest(".portlet-body");
        var error = $form.attr("data-error-display");
        var ajax = $form.attr("data-ajax");
        var url = $form.attr("action");

        if ($('.form-actions .red', $form).length === 0 &&
            $('.modal-footer .red', $form).length === 0) {
            // alert('helloworld2');
            return;
        }

        if (ajax && !url) {
            alert('form-submit-always-should-be-given.');
            return;
        }

        if (ajax) {
            e.preventDefault();
        }

        $parsley.whenValid().done(function() {

            if (url && ajax) {

                clean_ajax_clonable();
                App.blockUI({
                    target: $el,
                    animate: true,
                    overlayColor: 'blue'
                });

                $form.ajaxSubmit({
                    target: $el.closest('.portlet').parent(),
                    // data: data,
                    success: function(data, $form, jqXHR, _) {
                        // App.scrollTo($(el)); // flash가 이동시켜줄거니까
                        // console.log(data, _, jqXHR, $form);
                        // var $portlet = $($form);
                        // var url = $portlet.find('.portlet-title .tools .reload').data('url');
                        // if (url) {
                        //     url = url.replace('/_', '/');
                        // }
                    },
                    // error: function(data, $form, jqXHR, _) {
                    //     App.unblockUI($el);
                    // },
                });
            }
            else {
                /* To prevent multiple-click */
                App.blockUI({
                    target: $el,
                    animate: true,
                    overlayColor: 'gray'
                });
                // form.submit();
                // alert('go!');
            }

        });

        if ($parsley.validate()) {
        }
    });

    $('body').on('click', '.portlet a[data-ajax="true"]', function(e, v1, v2, v3) {
        e.preventDefault();
        // console.log(e, v1, v2, v3);
        var $alink = $(e.target);
        var $portlet = $alink.closest('.portlet-body');
        console.log($alink, $portlet);
        if (!$alink.attr('href')) {
            // console.log('before', $alink);
            $alink = $alink.closest('a');
            // console.log('after', $alink);
            // alert($alink.attr('href'));
        }

        if ($alink.data('dismiss') == 'modal') {
            $alink.closest('modal').modal('toggle');
            $('body > .modal-backdrop').remove();
            $('body').removeClass('modal-open');
        }

        // alert($alink.attr('href'));
        // alert($alink.data('confirmation'));
        if ($alink.data('confirmation')) {
            var title = $alink.data('title') || _('정말 이 동작을 수행하시겠습니까?');
            var message = $alink.data('message') || '';
            var confirmText = $alink.data('confirm-button-text') || _('실행');
            var alert_message = '<b>' + title  + '</b> ' +
                    message +
                    '<div class="pull-right">' +
                    '<a data-ajax="true" href="' + $alink.attr('href') + '">' +
                    '<i class="fa fa-check"></i> '+ confirmText + '</a>';
            // console.log(alert_message);
            // console.log($alink.attr('href'));
            App.alert({
                container: $portlet,
                place: "prepend",
                type: "danger",
                message: alert_message,
                close: false, // make alert closable reset: false, // close all previouse alerts first focus: true, // auto scroll to the alert after shown closeInSeconds: 10000, // auto close after defined seconds
                icon: 'fa fa-exclamation-circle', // put icon class before the message });
                reset: true,
                focus: true,
            });
        }
        else {
            // $.get({
            //     url: $alink.attr('href'),
            //     success: function(resp) {
            //         // console.log($(this), $(this).closest('.portlet-wrapper'));
            //         // window.history.pushState({}, '', $alink.attr('href').replace('/_', '/'));
            //         var $el = $alink.closest('.portlet-wrapper');
            //         App.scrollTo($el);
            //         $el.html(resp);
            //         console.log($el);
            //         // alert($alink.attr('href'));
            //     },
            //     beforeSend: function(xhr) {
            //         xhr.setRequestHeader('X-Alt-Referer', 'http://abc.com');
            //     },
            // })
            var $el = $alink.closest('.portlet-wrapper');//.parent();
            console.log($el);
            if ($alink.data('target')) {
                App.addNewPortlet($el, $alink.attr('href'));
            }
            else {
                // App.addNewPortlet($el.parent(), $alink.attr('href'));
                // return;

                App.blockUI({
                    target: $el,
                    animate: true,
                    overlayColor: 'blue'
                });

                $.get($alink.attr('href'), function(resp) {
                    // console.log($(this), $(this).closest('.portlet-wrapper'));
                    // window.history.pushState({}, '', $alink.attr('href').replace('/_', '/'));
                    // App.scrollTo($el);
                    $el.html(resp);
                    // console.log($el);
                    // alert($alink.attr('href'));
                }).done(function() {
                    if ($el.data('display-header') === 'False') {
                        $('.portlet-title', $el).hide();
                    }
                    // App.scrollTo($portlet);
                }).fail(function() {
                    App.unblockUI($el);
                    App.alert({
                        container: $portlet,
                        place: "prepend",
                        type: "danger",
                        message: _('존재하지 않는 리소스이거나 혹은 문제가 발생해서 페이지를 열 수 없습니다.'),
                        close: false, // make alert closable reset: false, // close all previouse alerts first focus: true, // auto scroll to the alert after shown closeInSeconds: 10000, // auto close after defined seconds
                        icon: 'fa fa-exclamation-circle', // put icon class before the message });
                        reset: true,
                        focus: true,
                    });
                });
            }
        }
    });

    // $('body').on('click', '.portlet .portlet-body a[data-confirmation="true"]', function(e, v1, v2, v3) {
    //     e.preventDefault();
    //     // console.log(e, v1, v2, v3);
    //     var $alink = $(e.target);
    //     if ($alink.data('ajax')) {
    //         return;
    //     }
    //     var $portlet = $alink.closest('.portlet-body');
    //     var title = $alink.data('title') || '정말 이 동작을 수행하시겠습니까?';
    //     var message = $alink.data('message') || '';
    //     var confirmText = $alink.data('confirm-button-text') || '실행';

    //     App.alert({
    //         container: $portlet,
    //         place: "prepend",
    //         type: "danger",
    //         message: '<b>' + title  + '</b> ' + message + '<div class="pull-right"><a href="' + $alink.attr('href') + '"><i class="fa fa-check"></i> '+ confirmText + ' </a>',
    //         close: false, // make alert closable reset: false, // close all previouse alerts first focus: true, // auto scroll to the alert after shown closeInSeconds: 10000, // auto close after defined seconds
    //         icon: 'fa fa-exclamation-circle', // put icon class before the message });
    //         reset: true,
    //         focus: true,
    //     });
    // });

});

/* bootstrap-table */
(function ($) {
    'use strict';
    if ($.fn.bootstrapTable) {
        $.fn.bootstrapTable.locales['en-US'] = {
            formatLoadingMessage: function () {
                return _('데이터를 불러오는 중입니다...');
            },
            formatRecordsPerPage: function (pageNumber) {
                return gt.strargs('페이지별 %1개 보기', pageNumber);
            },
            formatShowingRows: function (pageFrom, pageTo, totalRows) {
                return gt.strargs('총 %1개의 데이터가 있습니다.', totalRows, pageFrom, pageTo);
            },
            formatSearch: function () {
                return _('검색');
            },
            formatNoMatches: function () {
                return _('조회된 데이터가 없습니다.');
            },
            formatRefresh: function () {
                return _('새로 고침');
            },
            formatToggle: function () {
                return _('전환');
            },
            formatColumns: function () {
                return _('컬럼 필터링');
            }
        };

        $.extend($.fn.bootstrapTable.defaults, $.fn.bootstrapTable.locales['en-US']);
    }

    // $.fn.portlet = function(options) {
    //     var settings = $.extend({
    //         title: 'helloworld',
    //     }, options);

    //     return;
    // };
})(jQuery);

