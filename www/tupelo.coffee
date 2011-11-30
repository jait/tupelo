# tupelo.coffee
# vim: sts=2 sw=2 et:

T = ($) ->

  my = {}
  my.debug = false

  # some constants
  my.NOLO = 0
  my.RAMI = 1
  my.VOTING = 1
  my.ONGOING = 2

  my.log = (msg) ->
    console.log msg if my.debug

  # Simple ajax timer using jQuery
  my.Timer = (url, interval, callback, params) ->

    @url = url
    @interval = interval
    @callback = callback
    @params = params # extra params for jQuery.ajax
    # to make the object available in callback closures
    me = this

    ajaxCallback = (result) ->
      me.callback result
      me.setTimer()

    ajaxError = (xhr, astatus, error) ->
      my.log "status: " + astatus
      my.log "error: " + error
      me.disable()

    getData = ->
      params =
        url: me.url
        success: ajaxCallback
        error: ajaxError
      
      # set extra params
      for key of me.params
        params[key] = me.params[key]  if me.params.hasOwnProperty(key)

      $.ajax params

    @setTimer = ->
      @timer = window.setTimeout(getData, @interval)
      this

    @setTimer()

  my.Timer::disable = ->
    if @timer
      window.clearTimeout @timer
      @timer = `undefined`
    this

  # Player
  class my.Player
    constructor: (name) ->
      @player_name = name

    fromJSON: (json) ->
      obj = eval("(" + json + ")")
      @fromObj obj

    fromObj: (obj) ->
      for prop of obj
        this[prop] = obj[prop]
      this

    toString: ->
      "" + @player_name + " (" + @id + ")"

  # Card
  suits = [
    name: "spades"
    html: "&#x2660;"
  ,
    name: "diamonds"
    html: "&#x2666;"
  ,
    name: "clubs"
    html: "&#x2663;"
  ,
    name: "hearts"
    html: "&#x2665;"
  ]

  valueToChar = (value) ->
    switch value
      when 11
        "J"
      when 12
        "Q"
      when 13
        "K"
      when 1, 14
        "A"
      else
        value + ""

  class my.Card
    constructor: (suit, value) ->
      @suit = suit
      @value = value

    toString: ->
      "" + valueToChar(@value) + " of " + suits[@suit].name

    toShortString: ->
      "" + valueToChar(@value) + suits[@suit].html

    toShortHtml: ->
      "<span class=\"" + suits[@suit].name + "\">" + @toShortString() + "</span>"

  my

(jQuery)
