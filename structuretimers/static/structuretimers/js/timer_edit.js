$(document).ready(function () {
    const elem = document.getElementById('dataExport');
    const select2SolarSystemsUrl = elem.getAttribute('data-select2SolarSystemsUrl');
    const select2StructureTypesUrl = elem.getAttribute('data-select2StructureTypesUrl');
    const myTheme = "bootstrap"
    const isNightMode = JSON.parse(document.getElementById('night-mode-data').textContent);
    const datetimepickerTheme = isNightMode ? 'dark' : 'default'
    let languageCode = JSON.parse(document.getElementById('language-code-data').textContent);

    // mapping of language codes from Django to datetimepicker widget
    if (languageCode === "zh-hans") {
        languageCode = "zh";
    }

    $('.select2-solar-systems').select2({
        ajax: {
            url: select2SolarSystemsUrl,
            dataType: 'json'
        },
        theme: myTheme,
        minimumInputLength: 2,
        placeholder: "Enter name of solar system",
        dropdownCssClass: "my_select2_dropdown"
    });

    $('.select2-structure-types').select2({
        ajax: {
            url: select2StructureTypesUrl,
            dataType: 'json'
        },
        theme: myTheme,
        minimumInputLength: 2,
        placeholder: "Enter name of structure type",
        dropdownCssClass: "my_select2_dropdown"
    });

    $('.select2-render').select2({
        theme: myTheme,
        dropdownCssClass: "my_select2_dropdown"
    });

    $.datetimepicker.setLocale(languageCode);
    $('#timer-date-field').datetimepicker({ format: 'Y-m-d H:i', theme: datetimepickerTheme });

    // Clear date field when time-remaining fields are used and vice versa
    $('.timer-time-remaining-field').focus(function () {
        $('#timer-date-field').val('')
    });

    $('#timer-date-field').focus(function () {
        $('.timer-time-remaining-field').val('')
    });
});
