

var projectLinkFormatter = function(value, row, _) {
    "use strict";
    console.log(value, row, _);
    return '<a href="' + Flask.url_for('project.index', {project_id: row.project.id}) + '">' + row.project.title + '</a>';
};

var ProjectGroupPreferenceGlossaries = function() {

    return {
        init: function() {
            var $table = $('#project-group-glossaries-table');
            $table.bootstrapTable();

            // var $dialog = $('#project-pref-modal');
            // $dialog.on('hide.bs.modal', function (event) {
            //     $table.bootstrapTable('refresh');
            // });
        },
    };
}();
