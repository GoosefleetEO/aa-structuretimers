/* return duration as countdown string */
function durationToCountdownStr(duration) {
    var out = "";
    if (duration.years()) {
        out += duration.years() + 'y ';
    }
    if (duration.months()) {
        out += duration.months() + 'm ';
    }
    if (duration.days()) {
        out += duration.days() + 'd ';
    }
    return out + duration.hours() + "h " + duration.minutes() + "m " + duration.seconds() + "s";
}

function getCurrentEveTimeString() {
    return moment().utc().format('dddd LL HH:mm:ss')
}

/* eve clock and timer countdown feature */
function updateClock() {
    document.getElementById("current-time").innerHTML =
        moment().utc().format('YYYY-MM-DD HH:mm:ss');
}

/* return countdown to given date as string */
function dateToCountdownStr(date) {
    duration = moment.duration(moment(date).utc() - moment(), 'milliseconds');
    if (duration > 0) {
        return durationToCountdownStr(duration);
    }
    else {
        return 'ELAPSED';
    }
}

/* return local time and countdown string to given date as HTML*/
function localTimeOutputHtml(date) {
    return moment(date).format("ddd @ LT") + '<br>' + dateToCountdownStr(date);
}

$(document).ready(function () {

    /* retrieve generated data from HTML page */
    var elem = document.getElementById('dataExport');
    var listDataCurrentUrl = elem.getAttribute('data-listDataCurrentUrl');
    var listDataPastUrl = elem.getAttribute('data-listDataPastUrl');
    var getTimerDataUrl = elem.getAttribute('data-getTimerDataUrl');
    var titleSolarSystem = elem.getAttribute('data-titleSolarSystem');
    var titleRegion = elem.getAttribute('data-titleRegion');
    var titleStructureType = elem.getAttribute('data-titleStructureType');
    var titleTimerType = elem.getAttribute('data-titleTimerType');
    var titleObjective = elem.getAttribute('data-titleObjective');
    var titleOwner = elem.getAttribute('data-titleOwner');
    var titleVisibility = elem.getAttribute('data-titleVisibility');
    var hasPermOPSEC = (elem.getAttribute('data-hasPermOPSEC') == 'True');
    var dataTablesPageLength = Number(elem.getAttribute('data-dataTablesPageLength'));
    var dataTablesPaging = (elem.getAttribute('data-dataTablesPaging') == 'True');

    /* Update modal with requested timer */
    $('#modalTimerDetails').on('show.bs.modal', function (event) {
        var button = $(event.relatedTarget)
        var timer_pk = button.data('timerpk')
        var modal = $(this)
        $('#modal_div_data').hide()
        $('#modal_div_spinner').show()
        $.get(
            getTimerDataUrl.replace('pk_dummy', timer_pk),
            function (timer, status) {
                if (status == "success") {
                    modal
                        .find('.modal-body span')
                        .text(
                            `${timer['display_name']}`
                        );
                    if (timer['details_image_url'] != "") {
                        modal
                            .find('.modal-body label[for="timerboardImgScreenshot"]')
                            .show()
                        modal
                            .find('.modal-body img')
                            .attr("src", timer['details_image_url']);
                        modal
                            .find('.modal-body a')
                            .show()
                            .attr("href", timer['details_image_url']);
                    }
                    else {
                        modal
                            .find('.modal-body a')
                            .hide()
                        modal
                            .find('.modal-body label[for="timerboardImgScreenshot"]')
                            .hide()
                    }
                    if (timer['notes'] != "") {
                        modal
                            .find('.modal-body textarea')
                            .val(timer['notes']);
                    }
                    $('#modal_div_spinner').hide()
                    $('#modal_div_data').show()
                } else {
                    modal
                        .find('.modal-body span')
                        .html(
                            `<span class="text-error">Failed to load timer with ID ${timer_pk}</span>`
                        );
                }
            });
    });

    /* build dataTables */
    var columns = [
        { data: 'date' },
        { data: 'local_time' },
        { data: 'location' },
        { data: 'distance' },
        { data: 'structure_details' },
        { data: 'owner' },
        { data: 'name_objective' },
        { data: 'actions' },

        /* hidden columns */
        { data: 'system_name' },
        { data: 'region_name' },
        { data: 'structure_type_name' },
        { data: 'timer_type_name' },
        { data: 'objective_name' },
        { data: 'visibility' },
        { data: 'owner_name' },
        { data: 'opsec_str' }
    ];
    var idx_start = 8
    var filterDropDown = {
        columns: [
            {
                idx: idx_start,
                title: titleSolarSystem
            },
            {
                idx: idx_start + 1,
                title: titleRegion
            },
            {
                idx: idx_start + 2,
                title: titleStructureType
            },
            {
                idx: idx_start + 3,
                title: titleTimerType
            },
            {
                idx: idx_start + 4,
                title: titleObjective
            },
            {
                idx: idx_start + 5,
                title: titleVisibility
            },
            {
                idx: idx_start + 6,
                title: titleOwner,
                maxWidth: '12em'
            }
        ],
        bootstrap: true,
        autoSize: false
    };
    var lengthMenu = [[10, 25, 50, 100, -1], [10, 25, 50, 100, "All"]]
    if (hasPermOPSEC) {
        filterDropDown.columns.push({
            idx: idx_start + 7,
            title: 'OPSEC'
        })
    }
    var columnDefs = [
        { "sortable": false, "targets": [idx_start - 1] },
        {
            "visible": false, "targets": [
                idx_start,
                idx_start + 1,
                idx_start + 2,
                idx_start + 3,
                idx_start + 4,
                idx_start + 5,
                idx_start + 6,
                idx_start + 7
            ]
        },
        {
            "render": function (data, type, row) {
                return moment(data).utc().format("YYYY-MM-DD HH:mm");
            },
            "targets": 0
        },
        {
            "render": function (data, type, row) {
                return localTimeOutputHtml(data);
            },
            "targets": 1
        }
    ];
    $('#tab_timers_past').DataTable({
        ajax: {
            url: listDataPastUrl,
            dataSrc: '',
            cache: false
        },
        columns: columns,
        order: [[0, "desc"]],
        lengthMenu: lengthMenu,
        paging: dataTablesPaging,
        pageLength: dataTablesPageLength,
        filterDropDown: filterDropDown,
        columnDefs: columnDefs
    });
    var table_current = $('#tab_timers_current').DataTable({
        ajax: {
            url: listDataCurrentUrl,
            dataSrc: '',
            cache: false
        },
        columns: columns,
        order: [[0, "asc"]],
        lengthMenu: lengthMenu,
        paging: dataTablesPaging,
        pageLength: dataTablesPageLength,
        filterDropDown: filterDropDown,
        columnDefs: columnDefs,
        createdRow: function (row, data, dataIndex) {
            if (data['is_passed']) {
                $(row).addClass('active');
            }
            else if (data['is_important']) {
                $(row).addClass('warning');
            }
        }
    });

    function updateTimers() {
        table_current.rows().every(function () {
            var d = this.data();
            if (!d['is_passed']) {
                d['local_time'] = d['date']
                table_current
                    .row(this)
                    .data(d);
            }
        });
    }

    function timedUpdate() {
        updateClock();
        updateTimers();
    }

    // Start timed updates
    setInterval(timedUpdate, 1000);
});
