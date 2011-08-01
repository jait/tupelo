/* tupelo.js
 * vim: sts=4 sw=4 et:
*/
/*jslint devel: true, browser: true, sloppy: true, maxerr: 50, indent: 4 */

var T = (function ($) {
    var my = {};

    var debug = false;

    // some constants
    my.NOLO = 0;
    my.RAMI = 1;
    my.VOTING = 1;
    my.ONGOING = 2;

    my.log = function (msg) {
        if (debug) {
            console.log(msg);
        }
    };

    // Simple ajax timer using jQuery
    my.Timer = function (url, interval, callback, params) {

        this.url = url;
        this.interval = interval;
        this.callback = callback;
        this.params = params; // extra params for jQuery.ajax
        // to make the object available in callback closures
        var me = this;

        function ajaxCallback(result) {
            //my.log(me);
            me.callback(result);
            me.setTimer();
        }

        function ajaxError(xhr, astatus, error) {
            my.log("status: " + astatus);
            my.log("error: " + error);
            me.disable();
        }

        function getData() {
            //my.log("getData: " + me.url);
            var params = {url: me.url, success: ajaxCallback,
                error: ajaxError};
            // set extra params
            for (var key in me.params) {
                if (me.params.hasOwnProperty(key)) {
                    params[key] = me.params[key];
                }
            }
            $.ajax(params);
        }

        this.setTimer = function () {
            //my.log("setTimer " + this);
            //my.log("setting timeout to " + this.interval);
            this.timer = window.setTimeout(getData, this.interval);
            //my.log("timer: " + this.timer);
            return this;
        };

        this.setTimer();
    };

    my.Timer.prototype.disable = function () {
        if (this.timer) {
            window.clearTimeout(this.timer);
            this.timer = undefined;
        }
        return this;
    };

    // Player
    my.Player = function (name) {
        this.player_name = name;
    };

    my.Player.prototype.fromJSON = function (json) {
        var obj = eval("(" + json + ")");
        return this.fromObj(obj);
    };

    my.Player.prototype.fromObj = function (obj) {
        for (var prop in obj) {
            this[prop] = obj[prop];
        }
        return this;
    };

    my.Player.prototype.toString = function () {
        return "" + this.player_name + " (" + this.id + ")";
    };

    // Card
    var suits = [{name: "spades", html: "&#x2660;"},
            {name: "diamonds", html: "&#x2666;"},
            {name: 'clubs', html: "&#x2663;"},
            {name: 'hearts', html: "&#x2665;"}];

    function valueToChar(value) {
        switch (value) {
            case 11:
                return "J";
            case 12:
                return "Q";
            case 13:
                return "K";
            case 1: // fall through
            case 14:
                return "A";
            default:
                return (value + "");
        }
    }

    my.Card = function (suit, value) {
        this.suit = suit;
        this.value = value;
    };

    my.Card.prototype.toString = function () {
        return "" + valueToChar(this.value) + " of " + suits[this.suit].name;
    };

    my.Card.prototype.toShortString = function () {
        return "" + valueToChar(this.value) + suits[this.suit].html;
    };

    my.Card.prototype.toShortHtml = function () {
        return "<span class=\"" + suits[this.suit].name + "\">" + this.toShortString() + "</span>";
    };

    return my;
}(jQuery));
