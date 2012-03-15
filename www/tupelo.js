(function() {
  var $, T, root;
  var __hasProp = Object.prototype.hasOwnProperty;

  root = typeof exports !== "undefined" && exports !== null ? exports : this;

  $ = jQuery;

  T = {};

  T.debug = false;

  T.NOLO = 0;

  T.RAMI = 1;

  T.VOTING = 1;

  T.ONGOING = 2;

  T.log = function(msg) {
    if (T.debug) {
      return typeof console !== "undefined" && console !== null ? console.log(msg) : void 0;
    }
  };

  T.Timer = function(url, interval, callback, params) {
    var ajaxCallback, ajaxError, getData;
    var _this = this;
    this.url = url;
    this.interval = interval;
    this.callback = callback;
    this.params = params;
    ajaxCallback = function(result) {
      _this.callback(result);
      return _this.setTimer();
    };
    ajaxError = function(xhr, astatus, error) {
      T.log("status: " + astatus);
      T.log("error: " + error);
      return _this.disable();
    };
    getData = function() {
      var key, _ref;
      params = {
        url: _this.url,
        success: ajaxCallback,
        error: ajaxError
      };
      _ref = _this.params;
      for (key in _ref) {
        if (!__hasProp.call(_ref, key)) continue;
        params[key] = _this.params[key];
      }
      return $.ajax(params);
    };
    this.setTimer = function() {
      this.timer = window.setTimeout(getData, this.interval);
      return this;
    };
    return this.setTimer();
  };

  T.Timer.prototype.disable = function() {
    if (this.timer) {
      window.clearTimeout(this.timer);
      this.timer = null;
    }
    return this;
  };

  T.Player = (function() {

    function Player(name) {
      this.player_name = name;
    }

    Player.prototype.fromJSON = function(json) {
      var obj;
      obj = eval("(" + json + ")");
      return this.fromObj(obj);
    };

    Player.prototype.fromObj = function(obj) {
      var prop;
      for (prop in obj) {
        this[prop] = obj[prop];
      }
      return this;
    };

    Player.prototype.toString = function() {
      return "" + this.player_name + " (" + this.id + ")";
    };

    return Player;

  })();

  T.Card = (function() {
    var suits, valueToChar;

    function Card(suit, value) {
      this.suit = suit;
      this.value = value;
    }

    suits = [
      {
        name: "spades",
        html: "&#x2660;"
      }, {
        name: "diamonds",
        html: "&#x2666;"
      }, {
        name: "clubs",
        html: "&#x2663;"
      }, {
        name: "hearts",
        html: "&#x2665;"
      }
    ];

    valueToChar = function(value) {
      switch (value) {
        case 11:
          return "J";
        case 12:
          return "Q";
        case 13:
          return "K";
        case 1:
        case 14:
          return "A";
        default:
          return value + "";
      }
    };

    Card.prototype.toString = function() {
      return "" + valueToChar(this.value) + " of " + suits[this.suit].name;
    };

    Card.prototype.toShortString = function() {
      return "" + valueToChar(this.value) + suits[this.suit].html;
    };

    Card.prototype.toShortHtml = function() {
      return "<span class=\"" + suits[this.suit].name + "\">" + this.toShortString() + "</span>";
    };

    return Card;

  })();

  root.T = T;

}).call(this);
