if (typeof String.prototype.startsWith != 'function') {
    String.prototype.startsWith = function (str) {
        return str.length > 0 && this.substring(0, str.length) === str;
    }
};

if (typeof String.prototype.endsWith != 'function') {
    String.prototype.endsWith = function (str) {
        return str.length > 0 && this.substring(this.length - str.length, this.length) === str;
    }
};

if (typeof String.prototype.replaceAll != 'function') {
    String.prototype.replaceAll = function (search, replacement) {
        var target = this;
        return target.replace(new RegExp(search, 'g'), replacement);
    }
};

function jsonStringFilter(jsonString) {
    return jsonString.replace(/\n/g, "\\n").replace(/\r/g, "\\r").replace(/\t/g, "\\t").replace(/&quot;/g, '\"');
}

function sfStringToDate(dateTimeString) {
    if (dateTimeString == null || dateTimeString.length == 0)
        return null;

    if (dateTimeString.indexOf("T")>=0 && dateTimeString.endsWith("Z"))
        return new Date(dateTimeString);

    var segments, dateSegs, timeSegs;
    segments = dateTimeString.split("T");
    if (segments.length < 2)
        segments = dateTimeString.split(" ");

    if (segments.length >= 2) {
        dateSegs = segments[0].split("-");
        timeSegs = segments[1].split(":");
        if (segments[2] != null)
            return new Date(dateSegs[0] + "-" + sfFormatNumberLength(dateSegs[1], 2) + "-" + sfFormatNumberLength(dateSegs[2], 2) + "T" + sfFormatNumberLength(timeSegs[0], 2) + ":" + sfFormatNumberLength(timeSegs[1], 2) + ":" + sfFormatNumberLength(timeSegs[2], 2) + segments[2]);
        else
            return new Date(dateSegs[0] + "-" + sfFormatNumberLength(dateSegs[1], 2) + "-" + sfFormatNumberLength(dateSegs[2], 2) + "T" + sfFormatNumberLength(timeSegs[0], 2) + ":" + sfFormatNumberLength(timeSegs[1], 2) + ":" + sfFormatNumberLength(timeSegs[2], 2) + "Z");
    }
    else
        return null;
}

function sfDateToString(dateTimeObj) {
    if (dateTimeObj == null)
        return '';

    var year = dateTimeObj.getFullYear();
    var month = dateTimeObj.getMonth() + 1;
    var date = dateTimeObj.getDate();
    var hour = dateTimeObj.getHours();
    var minutes = dateTimeObj.getMinutes();
    var second = dateTimeObj.getSeconds();
    var timezoneInHour = dateTimeObj.getTimezoneOffset() / 60;
    var timeDiff = sfFormatNumberLength(Math.abs(timezoneInHour), 2);
    var tz;
    if (timezoneInHour > 0)
        tz = "-" + timeDiff + ":00";
    else
        tz = "+" + timeDiff + ":00";
    return year + "-" + sfFormatNumberLength(month, 2) + "-" + sfFormatNumberLength(date, 2) + " " + sfFormatNumberLength(hour, 2) + ":" + sfFormatNumberLength(minutes, 2) + ":" + sfFormatNumberLength(second, 2) + " " + tz;
}

function sfFormatNumberLength(num, length) {
    var r = "" + num;
    while (r.length < length) {
        r = "0" + r;
    }
    return r;
}

function sfGetDateTimeNowByTimezone(timzoneOffset) {
    var tzString = new Date(new Date().getTime() + timzoneOffset * 3600 * 1000);
    var month = eval(tzString.getUTCMonth() + 1);
    var tzUTCString = tzString.getUTCFullYear() + "-" + sfFormatNumberLength(month, 2) + "-" + sfFormatNumberLength(tzString.getUTCDate(), 2) + " " + sfFormatNumberLength(tzString.getUTCHours(), 2) + ":" + sfFormatNumberLength(tzString.getUTCMinutes(), 2) + ":" + sfFormatNumberLength(tzString.getUTCSeconds(), 2);

    if (timzoneOffset > 0)
        tzUTCString = tzUTCString + " +" + sfFormatNumberLength(Math.abs(timzoneOffset), 2) + ":00";
    else
        tzUTCString = tzUTCString + " -" + sfFormatNumberLength(Math.abs(timzoneOffset), 2) + ":00";

    return tzUTCString;
}

function sfIsJson(str) {
    try {
        if (str.indexOf('{') < 0)
            return false;
        JSON.parse(str);
    } catch (e) {
        return false;
    }
    return true;
}

function sfBacktoHomeIndex()
{
    var url = window.location.href;
    var arr = url.split("/");
    window.location.href = arr[0] + "//" + arr[2];    
}

function Comparator(a, b) {
    if (a[0] < b[0]) return -1;
    if (a[0] > b[0]) return 1;
    return 0;
}