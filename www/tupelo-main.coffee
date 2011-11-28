# tupelo-main.coffee
# vim: sts=2 sw=2 et:

$ = jQuery

$(document).ready ->
  # status object
  tupelo =
    game_state: {}
    events: []

  states =
    initial:
      show: [ "#register_form" ]
      hide: [ "#quit_form", "#games", "#players", "#my_game", "#game" ]
      change: ->
        reg = $("#register_name")
        reg.addClass "initial"
        reg.val "Your name"
        return

    registered:
      show: [ "#quit_form", "#games", "#players", "#game_create_form" ]
      hide: [ "#register_form", "#my_game", "#game" ]
      change: ->
        if not tupelo.list_timer?
          tupelo.list_timer = setInterval(updateLists, 5000)

    gameCreated:
      show: [ "#my_game" ]
      hide: [ "#game_create_form" ]

    inGame:
      show: [ "#game" ]
      hide: [ "#games", "#players", "#my_game" ]

  # change the current state
  setState = (state, effectDuration) ->
    st = states[state]
    $(elem).hide effectDuration for elem in st.hide
    $(elem).show effectDuration for elem in st.show
    st.change() if st.change?

  escapeHtml = (str) ->
    str.replace("<", "&lt;").replace ">", "&gt;"

  dbg = ->
    $("#debug").html JSON.stringify(tupelo) if T.debug

  # generic ajax error callback
  ajaxErr = (xhr, astatus, error) ->
    handled = false
    # 403 is for game and rule errors
    if xhr.status is 403
      # parse from json
      jsonErr = eval "(" + xhr.responseText + ")"
      if jsonErr.message?
        window.alert jsonErr.message
        handled = true
    else
      T.log "status: " + astatus
      T.log "error: " + error
    handled

  hello = ->
    $.ajax
      url: "/ajax/hello"
      success: (result) ->
        T.log "Server version: " + result.version
        # are we already logged in?
        if result.player?
          tupelo.player = new T.Player result.player.player_name
          registerOk result.player
          # are we in a game?
          if result.player.game_id?
            gameCreateOk result.player.game_id
      error: ajaxErr

  updateGameLinks = (disabledIds) ->
    gameJoinClicked = (event) ->
      # "game_join_ID"
      game_id = @id[10..]
      T.log "joining game " + game_id
      $.ajax
        url: "/ajax/game/enter"
        data:
          akey: tupelo.player.akey
          game_id: game_id
        success: gameCreateOk
        error: ajaxErr

    if tupelo.game_id?
      $("button.game_join").attr "disabled", true
      $("tr#game_id_" + tupelo.game_id).addClass "highlight"
    else
      $("button#" + id).attr "disabled", true for id in disabledIds
      $("button.game_join").click gameJoinClicked

  listGamesOk = (result) ->
    #T.log "listGamesOk"
    #T.log result
    html = ""
    disabledIds = []
    for own game_id of result
      html += "<tr id=\"game_id_#{game_id}\">"
      #players = []
      #for res in result[game_id]
      #  plr = new T.Player().fromObj res
      #  players.push plr.player_name
      players = (new T.Player().fromObj(res).player_name for res in result[game_id])

      html += "<td>" + escapeHtml(players.join(", ")) + "</td>"
      html += "<td class=\"game_list_actions\"><button class=\"game_join btn\" id=\"game_join_" + game_id + "\"><span><span>join</span></span></button></td>"
      html += "</tr>"
      disabledIds.push "game_join_#{game_id}" if players.length is 4

    $("#game_list table tbody").html html
    updateGameLinks disabledIds
    dbg()

  listPlayersOk = (result) ->
    T.log result
    html = ""
    for own player of result
      plr = new T.Player().fromObj(result[player])
      if plr.id isnt tupelo.player.id
        cls = if plr.game_id? then "class=\"in_game\" " else ""
        html += "<tr #{cls}id=\"player_id_" + plr.id + "\">"
        html += "<td>" + escapeHtml(plr.player_name) + "</td></tr>"

    $("#player_list table tbody").html html
    dbg()

  registerOk = (result) ->
    $("#name").val ""
    tupelo.player.id = result.id
    tupelo.player.akey = result.akey
    $.cookie "akey", result.akey
    T.log tupelo
    dbg()
    # clear game list if there was one previously
    $("#game_list table tbody").html ""
    $(".my_name").html escapeHtml(tupelo.player.player_name)
    updateLists()
    setState "registered", "fast"
    T.log "timer created"

  leftGame = ->
    if tupelo.event_fetch_timer?
      tupelo.event_fetch_timer.disable()
      tupelo.event_fetch_timer = null

    if tupelo.event_timer?
      clearTimeout tupelo.event_timer
      tupelo.event_timer = null

    tupelo.game_id = null
    tupelo.game_state = {}
    tupelo.hand = null
    tupelo.my_turn = null
    return

  leaveOk = (result) ->
    leftGame()
    dbg()
    updateLists()
    setState "registered", "fast"

  quitOk = (result) ->
    leftGame()
    if tupelo.list_timer?
      clearInterval tupelo.list_timer
      tupelo.list_timer = null

    $.cookie "akey", null
    tupelo.player = null
    T.log tupelo
    dbg()
    setState "initial", "fast"

  gameCreateOk = (result) ->
    tupelo.game_id = result
    T.log tupelo
    dbg()
    $("p#joined_game").html "joined game #{tupelo.game_id}"
    setState "gameCreated", "fast"
    tupelo.event_fetch_timer = new T.Timer("/ajax/get_events", 2000, eventsOk,
      data:
        akey: tupelo.player.akey
      )
    updateLists()

  cardPlayed = (event) ->
    T.log "cardPlayed"
    #T.log event
    table = $("#player_" + event.player.id + " .table")
    if table.length is 0
      T.log "player not found!"
      return true

    #table.hide()
    card = new T.Card(event.card.suit, event.card.value)
    table.html "<span style=\"display: none;\" class=\"card\">" + card.toShortHtml() + "</span>"
    table.children().show 500
    setTimeout processEvent, 500
    false

  messageReceived = (event) ->
    T.log "messageReceived"
    eventLog = $("#event_log")
    eventLog.append escapeHtml(event.sender) + ": " + escapeHtml(event.message) + "\n"
    eventLog.scrollTop eventLog[0].scrollHeight - eventLog.height()
    true

  # clear the table and resume event processing
  # called either from timeout or click event
  clearTable = ->
    clearTimeout tupelo.clear_timeout
    T.log "clearing table"
    $("#game_area .table").html ""
    $("#game_area table tbody").unbind "click"
    # re-enable event processing
    tupelo.event_timer = setTimeout(processEvent, 0)
    #T.log("trickPlayed: set event_timer to " + tupelo.event_timer)

  trickPlayed = (event) ->
    T.log "trickPlayed"
    # TODO: highlight the highest card
    # allow the user to clear the table and proceed by clicking the table
    $("#game_area table tbody").click clearTable
    # setting timeout to show the played trick for a longer time
    tupelo.clear_timeout = setTimeout(clearTable, 5000)
    false # this event is not handled yet

  getTeamPlayers = (team) ->
    # TODO: should we store these in JS instead of the DOM?
    [ $("#table_" + team + " .player_name").html(), $("#table_" + (team + 2) + " .player_name").html() ]

  updateGameState = (state) ->
    statusStr = ""
    for own key of state
      tupelo.game_state[key] = state[key]

    # show game status (voting, nolo, rami)
    if state.state is T.VOTING
      statusStr = "VOTING"
    else if state.state is T.ONGOING
      if state.mode is T.NOLO
        statusStr = "NOLO"
      else statusStr = "RAMI" if state.mode is T.RAMI

    statusStr = "<span>#{statusStr}</span>"
    statusStr += "<span>tricks: " + state.tricks[0] + " - " + state.tricks[1] + "</span>"

    if state.score?
      if state.score[0] > 0
        statusStr += "<span>score: " + escapeHtml(getTeamPlayers(0).join(" &amp; ")) + ": " + state.score[0] + "</span>"
      else if state.score[1] > 0
        statusStr += "<span>score: " + escapeHtml(getTeamPlayers(1).join(" &amp; ")) + ": " + state.score[1] + "</span>"
      else
        statusStr += "<span>score: 0</span>"

    $("#game_status").html statusStr
    # highlight the player in turn
    if state.turn_id?
      $(".player_data .player_name").removeClass "highlight_player"
      $("#player_" + state.turn_id + " .player_name").addClass "highlight_player"

    dbg()

  cardClicked = (event) ->
    # id is "card_X"
    cardId = $(this).find(".card").attr("id").slice(5)
    card = tupelo.hand[cardId]
    T.log card
    if card?
      $.ajax
        url: "/ajax/game/play_card"
        success: (result) ->
          tupelo.my_turn = false
          $("#hand .card").removeClass "card_selectable"
          # TODO: after playing a hand, this shows the next hand too quickly
          getGameState()

        error: (xhr, astatus, error) ->
          window.alert xhr.status + " " + error if ajaxErr(xhr, astatus, error) isnt true

        data:
          akey: tupelo.player.akey
          game_id: tupelo.game_id
          card: JSON.stringify(card)

    event.preventDefault()

  updateHand = (newHand) ->
    html = ""
    hand = []
    for item, i in newHand
      card = new T.Card(item.suit, item.value)
      hand.push card
      html += "<a class=\"selectable\" href=\"#\">" if tupelo.my_turn
      html += "<span class=\"card\" id=\"card_#{i}\">" + card.toShortHtml() + "</span>"
      html += "</a>" if tupelo.my_turn

    tupelo.hand = hand
    $("#hand").html html
    if tupelo.my_turn
      $("#hand .card").addClass "card_selectable"
      $("#hand a").click cardClicked

  getGameState = ->
    $.ajax
      url: "/ajax/game/get_state"
      success: (result) ->
        T.log result
        updateGameState result.game_state if result.game_state?
        updateHand result.hand if result.hand?

      error: ajaxErr
      data:
        akey: tupelo.player.akey
        game_id: tupelo.game_id

  turnEvent = (event) ->
    T.log "turnEvent"
    tupelo.my_turn = true # enables click callbacks for cards in hand
    getGameState()
    true

  stateChanged = (event) ->
    T.log "stateChanged"
    if event.game_state.state is T.VOTING # game started!
      startOk()
    else if event.game_state.state is T.ONGOING # VOTING -> ONGOING
      # allow the user to clear the table and proceed by clicking the table
      $("#game_area table tbody").click clearTable
      # setting timeout to show the voted cards for a longer time
      tupelo.clear_timeout = setTimeout(clearTable, 5000)
      return false
    true

  processEvent = ->
    handled = true
    if tupelo.events.length is 0
      T.log "no events to process"
      tupelo.event_timer = null
      return

    event = tupelo.events.shift()
    updateGameState event.game_state if event.game_state?
    switch event.type
      when 1
        handled = cardPlayed(event)
      when 2
        handled = messageReceived(event)
      when 3
        handled = trickPlayed(event)
      when 4
        handled = turnEvent(event)
      when 5
        handled = stateChanged(event)
      else
        T.log "unknown event " + event.type

    if handled is true
      tupelo.event_timer = setTimeout(processEvent, 0)

  eventsOk = (result) ->
    ###
    if (result.length > 0)
      eventLog = $("#event_log")
      eventLog.append(JSON.stringify(result) + "\n")
      eventLog.scrollTop(eventLog[0].scrollHeight - eventLog.height())
    ###
    # push events to queue
    tupelo.events.push event for event in result

    if tupelo.events.length > 0 and not tupelo.event_timer?
      tupelo.event_timer = setTimeout(processEvent, 0)

    dbg()

  gameInfoOk = (result) ->
    T.log "gameInfoOk"
    T.log result
    myIndex = 0
    # find my index
    for pl, i in result
      if pl.id is tupelo.player.id
        myIndex = i
        break

    for pl, i in result
      # place where the player goes when /me is always at the bottom
      index = (4 + i - myIndex) % 4
      # set player id and name
      $("#table_" + index + " .player_data").attr "id", "player_" + pl.id
      $("#player_" + pl.id + " .player_name").html escapeHtml(pl.player_name)

    return

  startOk = (result) ->
    if tupelo.list_timer?
      clearInterval tupelo.list_timer
      tupelo.list_timer = null

    $("#event_log").html ""
    setState "inGame"
    $.ajax
      url: "/ajax/game/get_info"
      success: gameInfoOk
      error: ajaxErr
      data:
        game_id: tupelo.game_id

    getGameState()
    dbg()

  updateLists = ->
    $.ajax
      url: "/ajax/game/list"
      success: listGamesOk
      error: ajaxErr

    $.ajax
      url: "/ajax/player/list"
      success: listPlayersOk
      error: ajaxErr
      data:
        akey: tupelo.player.akey

  # bind DOM events

  $("#echo_ajax").click ->
    text = $("#echo").val()
    $.ajax
      url: "/ajax/echo"
      data:
        test: text
      success: (result) ->
        $("#echo_result").html escapeHtml(result)
        $("#echo").val ""
      error: ajaxErr

  $("#register_btn").click ->
    input = $("#register_name")
    name = input.val()
    if not name or input.hasClass("initial")
      alert "Please enter your name first"
      return

    tupelo.player = new T.Player(name)
    T.log tupelo
    $.ajax
      url: "/ajax/player/register"
      data:
        player: JSON.stringify(tupelo.player)
      success: registerOk
      error: ajaxErr

  # sign in by pressing enter
  $("#register_name").keyup (event) ->
    $("#register_btn").click() if (event.keyCode or event.which) is 13

  $("#register_name").focus (event) ->
    if $(this).hasClass("initial")
      $(this).val ""
      $(this).removeClass "initial"

  $("#quit_btn").click ->
    $.ajax
      url: "/ajax/player/quit"
      data:
        akey: tupelo.player.akey
      success: quitOk
      error: (xhr, astatus, error) ->
        quitOk() if ajaxErr(xhr, astatus, error) is true

  $(".game_leave_btn").click ->
    # TODO: should we cancel timers already here?
    $.ajax
      url: "/ajax/game/leave"
      data:
        akey: tupelo.player.akey
        game_id: tupelo.game_id
      success: leaveOk
      error: (xhr, astatus, error) ->
        leaveOk() if ajaxErr(xhr, astatus, error) is true

  $("#game_create_btn").click ->
    # TODO: should we cancel timers already here?
    $.ajax
      url: "/ajax/game/create"
      data:
        akey: tupelo.player.akey
      success: gameCreateOk
      error: ajaxErr

  $("#game_start").click ->
    $.ajax
      url: "/ajax/game/start"
      data:
        akey: tupelo.player.akey
        game_id: tupelo.game_id
      success: startOk
      error: ajaxErr

  $("#game_start_with_bots").click ->
    $.ajax
      url: "/ajax/game/start_with_bots"
      data:
        akey: tupelo.player.akey
        game_id: tupelo.game_id
      success: startOk
      error: ajaxErr

  if T.debug is true
    $("#debug").click ->
      $(this).toggle()
  else
    $("#debug").hide()

  # leave the game when the user leaves the page
  $(window).unload ->
    if tupelo.game_id?
      $.ajax
        url: "/ajax/game/leave"
        async: false
        data:
          akey: tupelo.player.akey
          game_id: tupelo.game_id

  # show a confirmation if the browser supports it
  window.onbeforeunload = (e) ->
    if not tupelo.game_id?
      return `undefined` # no dialog
    e = e or window.event
    msg = "By leaving the page you will also leave the game."
    e.returnValue = msg if e
    msg

  # and finally, contact the server
  hello()
  setState "initial"

