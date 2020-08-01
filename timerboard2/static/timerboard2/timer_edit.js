$(document).ready(function () {
    var elem = document.getElementById('dataExport');
    var select2SolarSystemsUrl = elem.getAttribute('data-select2SolarSystemsUrl');
    var select2StructureTypesUrl = elem.getAttribute('data-select2StructureTypesUrl');
    var myTheme = "bootstrap"

    $('.select2-solar-systems').select2({
        ajax: {
            url: select2SolarSystemsUrl,
            dataType: 'json'
        },
        theme: myTheme,
        minimumInputLength: 2,
    });

    $('.select2-structure-types').select2({
        ajax: {
            url: select2StructureTypesUrl,
            dataType: 'json'
        },
        theme: myTheme,
        minimumInputLength: 2
    });

    $('.select2-render').select2({
        theme: myTheme
    });
});