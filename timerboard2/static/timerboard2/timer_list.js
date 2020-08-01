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

    /* Update modal with requested timer */
    $('#modalTimerDetails').on('show.bs.modal', function (event) {
        var button = $(event.relatedTarget)
        var timer_pk = button.data('timerpk')
        var modal = $(this)
        $.get(
            getTimerDataUrl.replace('pk_dummy', timer_pk),
            function (timer, status) {
                if (status == "success") {
                    modal
                        .find('.modal-body span')
                        .text(
                            `${timer['structure_display_name']} @ ${timer['eve_time']}`
                        );
                    modal
                        .find('.modal-body img')
                        .attr("src", timer['details_image_url']);
                    modal
                        .find('.modal-body a')
                        .attr("href", timer['details_image_url']);
                    modal
                        .find('.modal-body textarea')
                        .val(timer['notes']);
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
        { data: 'owner_name' },
        { data: 'visibility' },
        { data: 'opsec' }
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
                title: titleOwner
            },
            {
                idx: idx_start + 6,
                title: titleVisibility
            }
        ],
        bootstrap: true,
        autoSize: false
    };
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
        filterDropDown: filterDropDown,
        columnDefs: columnDefs,
        createdRow: function (row, data, dataIndex) {
            if (data['is_important']) {
                $(row).addClass('warning');
            }
            else if (data['is_passed']) {
                $(row).addClass('active');
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
                eve_time = moment(d['eve_time']).utc()
                eve_time_str = eve_time.format('YYYY-MM-DD HH:mm')
                duration = moment.duration(
                    eve_time - moment(), 'milliseconds'
                );
                if (duration > 0) {
                    countdown_str = getDurationString(duration);
                }
                else {
                    countdown_str = 'EXPIRED';
                }
                d['time'] = eve_time_str + '<br>' + countdown_str;
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