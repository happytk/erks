/**
 * @author: happytk (wecanfly@sk.com)
 * @version: v1.0.0
 */

(function ($) {
    'use strict';
    var sprintf = $.fn.bootstrapTable.utils.sprintf;

    var TYPE_NAME = {
        // json: 'JSON',
        // xml: 'XML',
        // png: 'PNG',
        // csv: 'CSV',
        // txt: 'TXT',
        // sql: 'SQL',
        // doc: 'MS-Word',
        excel: 'MS-Excel',
        // xlsx: 'MS-Excel (OpenXML)',
        // powerpoint: 'MS-Powerpoint',
        // pdf: 'PDF'
    };

    $.extend($.fn.bootstrapTable.defaults, {
        export: false,
        exportDataType: 'basic', // basic, all, selected
        // 'json', 'xml', 'png', 'csv', 'txt', 'sql', 'doc', 'excel', 'powerpoint', 'pdf'
        exportTypes: ['json', 'xml', 'csv', 'txt', 'sql', 'excel'],
        exportOptions: {},
        exportEndpoint: '',
        exportEndpointKwargs: '',
    });

    $.extend($.fn.bootstrapTable.defaults.icons, {
        export: 'glyphicon-export icon-share'
    });

    $.extend($.fn.bootstrapTable.locales, {
        formatExport: function () {
            return 'Export data';
        }
    });
    $.extend($.fn.bootstrapTable.defaults, $.fn.bootstrapTable.locales);

    var BootstrapTable = $.fn.bootstrapTable.Constructor,
        _initToolbar = BootstrapTable.prototype.initToolbar;

    BootstrapTable.prototype.initToolbar = function () {
        this.showToolbar = this.options.showExport;

        _initToolbar.apply(this, Array.prototype.slice.apply(arguments));

        if (this.options.showExport) {
            var that = this,
                $btnGroup = this.$toolbar.find('>.btn-group'),
                $export = $btnGroup.find('div.export');

            if (!$export.length) {
                $export = $([
                    '<div class="export btn-group">',
                        '<button class="btn' +
                            sprintf(' btn-%s', this.options.buttonsClass) +
                            sprintf(' btn-%s', this.options.iconSize) +
                            ' dropdown-toggle" aria-label="export type" ' +
                            'title="' + this.options.formatExport() + '" ' +
                            'data-toggle="dropdown" type="button">',
                            sprintf('<i class="%s %s"></i> ', this.options.iconsPrefix, this.options.icons.export),
                            '<span class="caret"></span>',
                        '</button>',
                        '<ul class="dropdown-menu" role="menu">',
                        '</ul>',
                    '</div>'].join('')).appendTo($btnGroup);

                var $menu = $export.find('.dropdown-menu'),
                    exportTypes = this.options.exportTypes;

                if (typeof this.options.exportTypes === 'string') {
                    var types = this.options.exportTypes.slice(1, -1).replace(/ /g, '').split(',');

                    exportTypes = [];
                    $.each(types, function (i, value) {
                        exportTypes.push(value.slice(1, -1));
                    });
                }
                $.each(exportTypes, function (i, type) {
                    if (TYPE_NAME.hasOwnProperty(type)) {
                        $menu.append(['<li role="menuitem" data-type="' + type + '">',
                                '<a href="javascript:void(0)">',
                                    TYPE_NAME[type],
                                '</a>',
                            '</li>'].join(''));
                    }
                });

                $menu.find('li').click(function () {
                    var type = $(this).data('type'),
                        doExport = function () {
                            var $portlet = that.$el.closest('.portlet-wrapper');
                            App.blockUI({
                                target: $portlet,
                                // animate: true,
                                boxed: true,
                                overlayColor: 'blue',
                                message: 'Exporting...'
                            });
                            var $box = $('.loading-message-boxed span', $portlet);
                            $.ajax({
                                url: Flask.url_for('exporter._exporter'),
                                type: 'post',
                                contentType: "application/json;charset=utf-8",
                                dataType: 'json',
                                data: JSON.stringify(
                                    $.extend({},
                                             {url_params: that.options._xhr_data},
                                             {url: that.options.url},
                                             {columns: that.options.columns[0]},
                                             {endpoint: that.options.exportEndpoint,
                                              endpoint_kwargs: that.options.exportEndpointKwargs}
                                    )
                                ),
                                success: function(resp) {
                                    console.log(resp);
                                    if(typeof(EventSource)==="undefined") {
                                        alert("Sorry, your browser does not support server-sent events...");
                                    }
                                    var source=new EventSource(Flask.url_for('exporter._run', {exporter_id: resp.id}));
                                    source.onmessage=function(event) {
                                        $box.html('<p>'+event.data+'</p>');
                                    };
                                    source.onopen=function(event) {
                                        $box.html('<p>시작합니다.</p>');
                                    };
                                    source.addEventListener('failed', function(event) {
                                        this.close();
                                        // $table.bootstrapTable('refresh');
                                        // App.unblockUI($portlet);
                                        // swal('엑셀 업로드에 실패했습니다.', event.data, 'error');
                                    }, false);
                                    source.addEventListener('completed', function(event) {
                                        this.close();
                                        // $table.bootstrapTable('refresh');
                                        App.unblockUI($portlet);

                                        // var ret = JSON.parse(event.data);
                                        swal({
                                            title: '완료되었습니다.',
                                            text: event.data,
                                            type: 'success',
                                            html: true,
                                        });
                                    }, false);
                                },
                            });

                            // that.$el.tableExport($.extend({}, that.options.exportOptions, {
                            //     type: type,
                            //     escape: false
                            // }));
                        };

                    if (that.options.exportDataType === 'all' && that.options.pagination) {
                        that.$el.one(that.options.sidePagination === 'server' ? 'post-body.bs.table' : 'page-change.bs.table', function () {
                            doExport();
                            that.togglePagination();
                        });
                        that.togglePagination();
                    } else if (that.options.exportDataType === 'selected') {
                        var data = that.getData(),
                            selectedData = that.getAllSelections();

                        // Quick fix #2220
                        if (that.options.sidePagination === 'server') {
                            data = {total: that.options.totalRows};
                            data[that.options.dataField] = that.getData();

                            selectedData = {total: that.options.totalRows};
                            selectedData[that.options.dataField] = that.getAllSelections();
                        }

                        that.load(selectedData);
                        doExport();
                        that.load(data);
                    } else {
                        doExport();
                    }
                });
            }
        }
    };
})(jQuery);