# tupelo.coffee
# vim: sts=2 sw=2 et:

root = exports ? this
$ = jQuery

T = {}
T.debug = false

# some constants
T.NOLO = 0
T.RAMI = 1
T.VOTING = 1
T.ONGOING = 2

T.log = (msg) ->
  console?.log msg if T.debug

# Simple ajax timer using jQuery
T.Timer = (url, interval, callback, params) ->

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
    T.log "status: " + astatus
    T.log "error: " + error
    me.disable()

  getData = ->
    params =
      url: me.url
      success: ajaxCallback
      error: ajaxError

    # set extra params
    for own key of me.params
      params[key] = me.params[key]

    $.ajax params

  @setTimer = ->
    @timer = window.setTimeout(getData, @interval)
    this

  @setTimer()

T.Timer::disable = ->
  if @timer
    window.clearTimeout @timer
    @timer = null
  this

# Player
class T.Player
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
class T.Card
  constructor: (suit, value) ->
    @suit = suit
    @value = value

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

  toString: ->
    "" + valueToChar(@value) + " of " + suits[@suit].name

  toShortString: ->
    "" + valueToChar(@value) + suits[@suit].html

  toShortHtml: ->
    "<span class=\"" + suits[@suit].name + "\">" + @toShortString() + "</span>"

# finally, export T to global object
root.T = T

