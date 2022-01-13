/* return duration as countdown string */
function durationToCountdownStr(duration) {
    let out = "";
    if (duration.years()) {
        out += duration.years() + "y ";
    }
    if (duration.months()) {
        out += duration.months() + "m ";
    }
    if (duration.days()) {
        out += duration.days() + "d ";
    }
    return (
        out +
        duration.hours() +
        "h " +
        duration.minutes() +
        "m " +
        duration.seconds() +
        "s"
    );
}

function getCurrentEveTimeString() {
    return moment().utc().format("dddd LL HH:mm:ss");
}

/* eve clock and timer countdown feature */
function updateClock() {
    document.getElementById("current-time").innerHTML = moment()
        .utc()
        .format("YYYY-MM-DD HH:mm:ss");
}

/* return countdown to given date as string */
function dateToCountdownStr(date) {
    let duration = moment.duration(moment(date).utc() - moment(), "milliseconds");
    if (duration > 0) {
        return durationToCountdownStr(duration);
    } else {
        return "ELAPSED";
    }
}

/* return local time and countdown string to given date as HTML*/
function localTimeOutputHtml(date) {
    return moment(date).format("ddd @ LT") + "<br>" + dateToCountdownStr(date);
}

function createVisibleColumDef(idxStart) {
    return {
        visible: false,
        targets: [
            idxStart,
            idxStart + 1,
            idxStart + 2,
            idxStart + 3,
            idxStart + 4,
            idxStart + 5,
            idxStart + 6,
            idxStart + 7,
        ],
    };
}

function createFilterDropDown(
    idxStart,
    hasPermOPSEC,
    titleSolarSystem,
    titleRegion,
    titleStructureType,
    titleTimerType,
    titleObjective,
    titleVisibility,
    titleOwner
) {
    var obj = {
        columns: [
            {
                idx: idxStart,
                title: titleSolarSystem,
            },
            {
                idx: idxStart + 1,
                title: titleRegion,
            },
            {
                idx: idxStart + 2,
                title: titleStructureType,
            },
            {
                idx: idxStart + 3,
                title: titleTimerType,
            },
            {
                idx: idxStart + 4,
                title: titleObjective,
            },
            {
                idx: idxStart + 5,
                title: titleVisibility,
            },
            {
                idx: idxStart + 6,
                title: titleOwner,
                maxWidth: "12em",
            },
        ],
        bootstrap: true,
        autoSize: false,
    };
    if (hasPermOPSEC) {
        obj.columns.push({
            idx: idxStart + 7,
            title: "OPSEC",
        });
    }
    return obj;
}

$(document).ready(function () {
    /* retrieve generated data from HTML page */
    const elem = document.getElementById("dataExport");
    const listDataCurrentUrl = elem.getAttribute("data-listDataCurrentUrl");
    const listDataPastUrl = elem.getAttribute("data-listDataPastUrl");
    const listDataTargetUrl = elem.getAttribute("data-listDataTargetUrl");
    const getTimerDataUrl = elem.getAttribute("data-getTimerDataUrl");
    const titleSolarSystem = elem.getAttribute("data-titleSolarSystem");
    const titleRegion = elem.getAttribute("data-titleRegion");
    const titleStructureType = elem.getAttribute("data-titleStructureType");
    const titleTimerType = elem.getAttribute("data-titleTimerType");
    const titleObjective = elem.getAttribute("data-titleObjective");
    const titleOwner = elem.getAttribute("data-titleOwner");
    const titleVisibility = elem.getAttribute("data-titleVisibility");
    const hasPermOPSEC = elem.getAttribute("data-hasPermOPSEC") == "True";
    const dataTablesPageLength = Number(elem.getAttribute("data-dataTablesPageLength"));
    const dataTablesPaging = elem.getAttribute("data-dataTablesPaging") == "True";
    const tabId = elem.getAttribute("data-tabId");

    /* activate selected tab */
    $('a[href="#' + tabId + '"]').tab("show");

    /* Update modal with requested timer */
    $("#modalTimerDetails").on("show.bs.modal", function (event) {
        const timer_pk = $(event.relatedTarget).data("timerpk");

        $("#modalLoadError").html("");
        $("#modalContent").hide();
        $("#modal_div_spinner").show();
        $("#modalContent").load(
            getTimerDataUrl.replace("pk_dummy", timer_pk),
            function (responseText, textStatus, req) {
                $("#modal_div_spinner").hide();
                $("#modalContent").show();
                if (textStatus == "error") {
                    console.log(req);
                    $("#modalLoadError").html(
                        '<p class="text-danger">An unexpected error occured: ' +
                            req.status +
                            " " +
                            req.statusText +
                            '</p><p class="text-danger">' +
                            "Please close this window and try again.</p>"
                    );
                }
            }
        );
    });

    /* build dataTables */
    let columns = [
        {
            data: "date",
            render: function (data, type, row) {
                return moment(data).utc().format("YYYY-MM-DD HH:mm");
            },
        },
        {
            data: "local_time",
            render: function (data, type, row) {
                return localTimeOutputHtml(data);
            },
        },
        { data: "location" },
        {
            data: "distance",
            render: {
                _: "display",
                sort: "sort",
            },
        },
        { data: "structure_details" },
        { data: "owner" },
        { data: "name_objective" },
        { data: "actions" },

        /* hidden columns */
        { data: "system_name" },
        { data: "region_name" },
        { data: "structure_type_name" },
        { data: "timer_type_name" },
        { data: "objective_name" },
        { data: "visibility" },
        { data: "owner_name" },
        { data: "opsec_str" },
    ];
    let lengthMenu = [
        [10, 25, 50, 100, -1],
        [10, 25, 50, 100, "All"],
    ];
    let idxStart = 8;
    let columnDefs = [
        { sortable: false, targets: [idxStart - 1] },
        createVisibleColumDef(idxStart),
    ];

    $("#tbl_timers_past").DataTable({
        ajax: {
            url: listDataPastUrl,
            dataSrc: "",
            cache: false,
        },
        columns: columns,
        order: [[0, "desc"]],
        lengthMenu: lengthMenu,
        paging: dataTablesPaging,
        pageLength: dataTablesPageLength,
        filterDropDown: createFilterDropDown(
            idxStart,
            hasPermOPSEC,
            titleSolarSystem,
            titleRegion,
            titleStructureType,
            titleTimerType,
            titleObjective,
            titleVisibility,
            titleOwner
        ),
        columnDefs: columnDefs,
    });
    $("#tbl_preliminary").DataTable({
        ajax: {
            url: listDataTargetUrl,
            dataSrc: "",
            cache: false,
        },
        columns: [
            { data: "location" },
            {
                data: "distance",
                render: {
                    _: "display",
                    sort: "sort",
                },
            },
            { data: "structure_details" },
            { data: "owner" },
            { data: "name_objective" },
            {
                data: "last_updated_at",
                render: function (data, type, row) {
                    return moment(data).utc().format("YYYY-MM-DD HH:mm");
                },
            },
            { data: "actions" },
            /* hidden columns */
            { data: "system_name" },
            { data: "region_name" },
            { data: "structure_type_name" },
            { data: "timer_type_name" },
            { data: "objective_name" },
            { data: "visibility" },
            { data: "owner_name" },
            { data: "opsec_str" },
        ],
        order: [[5, "desc"]],
        lengthMenu: lengthMenu,
        paging: dataTablesPaging,
        pageLength: dataTablesPageLength,
        columnDefs: [createVisibleColumDef(7)],
        filterDropDown: createFilterDropDown(
            7,
            hasPermOPSEC,
            titleSolarSystem,
            titleRegion,
            titleStructureType,
            titleTimerType,
            titleObjective,
            titleVisibility,
            titleOwner
        ),
    });
    const table_current = $("#tbl_timers_current").DataTable({
        ajax: {
            url: listDataCurrentUrl,
            dataSrc: "",
            cache: false,
        },
        columns: columns,
        order: [[0, "asc"]],
        lengthMenu: lengthMenu,
        paging: dataTablesPaging,
        pageLength: dataTablesPageLength,
        filterDropDown: createFilterDropDown(
            idxStart,
            hasPermOPSEC,
            titleSolarSystem,
            titleRegion,
            titleStructureType,
            titleTimerType,
            titleObjective,
            titleVisibility,
            titleOwner
        ),
        columnDefs: columnDefs,
        createdRow: function (row, data, dataIndex) {
            if (data["is_passed"]) {
                $(row).addClass("active");
            } else if (data["is_important"]) {
                $(row).addClass("warning");
            }
        },
    });

    function updateTimers() {
        table_current.rows().every(function () {
            var d = this.data();
            if (!d["is_passed"]) {
                d["local_time"] = d["date"];
                table_current.row(this).data(d);
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
