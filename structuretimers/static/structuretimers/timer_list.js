/**
* Get a duration string like countdown.js
* e.g. "1y 2d 3h 4m 5s"
* @param duration moment.duration
*/
function getDurationString(duration) {
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
    var dataTablesPageLength = elem.getAttribute('data-dataTablesPageLength');
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
        { data: 'time' },
        { data: 'location' },
        { data: 'structure_details' },
        { data: 'owner' },
        { data: 'name_objective' },
        { data: 'creator' },
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
    var idx_start = 7
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
                title: titleOwner
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

    /* eve clock and timer countdown feature */
    function updateClock() {
        document.getElementById("current-time").innerHTML =
            moment().utc().format('YYYY-MM-DD HH:mm:ss');
    }

    function updateTimers() {
        table_current.rows().every(function () {
            var d = this.data();
            if (!d['is_passed']) {
                date = moment(d['date']).utc()
                date_str = date.format('YYYY-MM-DD HH:mm')
                duration = moment.duration(
                    date - moment(), 'milliseconds'
                );
                if (duration > 0) {
                    countdown_str = getDurationString(duration);
                }
                else {
                    countdown_str = 'ELAPSED';
                }
                d['time'] = date_str + '<br>' + countdown_str;
                table_current
                    .row(this)
                    .data(d)
                    .draw();
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