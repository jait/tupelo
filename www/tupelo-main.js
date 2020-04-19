(function() {
  var $;
  var __hasProp = Object.prototype.hasOwnProperty;

  $ = jQuery;

  $(document).ready(function() {
    var ajaxErr, cardClicked, cardPlayed, clearTable, dbg, escapeHtml, eventsOk, gameCreateOk, gameInfoOk, getGameState, getTeamPlayers, hello, leaveOk, leftGame, listGamesOk, listPlayersOk, messageReceived, processEvent, quitOk, registerOk, setState, startOk, stateChanged, states, trickPlayed, tupelo, turnEvent, updateGameLinks, updateGameState, updateHand, updateLists;
    tupelo = {
      game_state: {},
      events: []
    };
    states = {
      initial: {
        show: ["#register_form"],
        hide: ["#quit_form", "#games", "#players", "#my_game", "#game"],
        change: function() {
          var reg;
          reg = $("#register_name");
          reg.addClass("initial");
          reg.val("Your name");
        }
      },
      registered: {
        show: ["#quit_form", "#games", "#players", "#game_create_form"],
        hide: ["#register_form", "#my_game", "#game"],
        change: function() {
          if (!(tupelo.list_timer != null)) {
            return tupelo.list_timer = setInterval(updateLists, 5000);
          }
        }
      },
      gameCreated: {
        show: ["#my_game"],
        hide: ["#game_create_form"]
      },
      inGame: {
        show: ["#game"],
        hide: ["#games", "#players", "#my_game"]
      }
    };
    setState = function(state, effectDuration) {
      var elem, st, _i, _j, _len, _len2, _ref, _ref2;
      st = states[state];
      _ref = st.hide;
      for (_i = 0, _len = _ref.length; _i < _len; _i++) {
        elem = _ref[_i];
        $(elem).hide(effectDuration);
      }
      _ref2 = st.show;
      for (_j = 0, _len2 = _ref2.length; _j < _len2; _j++) {
        elem = _ref2[_j];
        $(elem).show(effectDuration);
      }
      if (st.change != null) return st.change();
    };
    escapeHtml = function(str) {
      return str.replace("<", "&lt;").replace(">", "&gt;");
    };
    dbg = function() {
      if (T.debug) return $("#debug").html(JSON.stringify(tupelo));
    };
    ajaxErr = function(xhr, astatus, error) {
      var handled, jsonErr;
      handled = false;
      if (xhr.status === 403) {
        jsonErr = eval("(" + xhr.responseText + ")");
        if (jsonErr.message != null) {
          window.alert(jsonErr.message);
          handled = true;
        }
      } else {
        T.log("status: " + astatus);
        T.log("error: " + error);
      }
      return handled;
    };
    hello = function() {
      return $.ajax({
        url: "/ajax/hello",
        success: function(result) {
          T.log("Server version: " + result.version);
          if (result.player != null) {
            tupelo.player = new T.Player(result.player.player_name);
            registerOk(result.player);
            if (result.player.game_id != null) {
              return gameCreateOk(result.player.game_id);
            }
          }
        },
        error: ajaxErr
      });
    };
    updateGameLinks = function(disabledIds) {
      var gameJoinClicked, id, _i, _len;
      gameJoinClicked = function(event) {
        var game_id;
        game_id = this.id.slice(10);
        T.log("joining game " + game_id);
        return $.ajax({
          url: "/ajax/game/enter",
          data: {
            akey: tupelo.player.akey,
            game_id: game_id
          },
          success: gameCreateOk,
          error: ajaxErr
        });
      };
      if (tupelo.game_id != null) {
        $("button.game_join").attr("disabled", true);
        return $("tr#game_id_" + tupelo.game_id).addClass("highlight");
      } else {
        for (_i = 0, _len = disabledIds.length; _i < _len; _i++) {
          id = disabledIds[_i];
          $("button#" + id).attr("disabled", true);
        }
        return $("button.game_join").click(gameJoinClicked);
      }
    };
    listGamesOk = function(result) {
      var disabledIds, game_id, html, players, res;
      html = "";
      disabledIds = [];
      for (game_id in result) {
        if (!__hasProp.call(result, game_id)) continue;
        html += "<tr id=\"game_id_" + game_id + "\">";
        players = (function() {
          var _i, _len, _ref, _results;
          _ref = result[game_id];
          _results = [];
          for (_i = 0, _len = _ref.length; _i < _len; _i++) {
            res = _ref[_i];
            _results.push(new T.Player().fromObj(res).player_name);
          }
          return _results;
        })();
        html += "<td>" + escapeHtml(players.join(", ")) + "</td>";
        html += "<td class=\"game_list_actions\"><button class=\"game_join btn\" id=\"game_join_" + game_id + "\"><span><span>join</span></span></button></td>";
        html += "</tr>";
        if (players.length === 4) disabledIds.push("game_join_" + game_id);
      }
      $("#game_list table tbody").html(html);
      updateGameLinks(disabledIds);
      return dbg();
    };
    listPlayersOk = function(result) {
      var cls, html, player, plr;
      T.log(result);
      html = "";
      for (player in result) {
        if (!__hasProp.call(result, player)) continue;
        plr = new T.Player().fromObj(result[player]);
        if (plr.id !== tupelo.player.id) {
          cls = plr.game_id != null ? "class=\"in_game\" " : "";
          html += ("<tr " + cls + "id=\"player_id_") + plr.id + "\">";
          html += "<td>" + escapeHtml(plr.player_name) + "</td></tr>";
        }
      }
      $("#player_list table tbody").html(html);
      return dbg();
    };
    registerOk = function(result) {
      $("#name").val("");
      tupelo.player.id = result.id;
      tupelo.player.akey = result.akey;
      Cookies.set("akey", result.akey);
      T.log(tupelo);
      dbg();
      $("#game_list table tbody").html("");
      $(".my_name").html(escapeHtml(tupelo.player.player_name));
      updateLists();
      setState("registered", "fast");
      return T.log("timer created");
    };
    leftGame = function() {
      if (tupelo.event_fetch_timer != null) {
        tupelo.event_fetch_timer.disable();
        tupelo.event_fetch_timer = null;
      }
      if (tupelo.event_timer != null) {
        clearTimeout(tupelo.event_timer);
        tupelo.event_timer = null;
      }
      tupelo.game_id = null;
      tupelo.game_state = {};
      tupelo.hand = null;
      tupelo.my_turn = null;
    };
    leaveOk = function(result) {
      leftGame();
      dbg();
      updateLists();
      return setState("registered", "fast");
    };
    quitOk = function(result) {
      leftGame();
      if (tupelo.list_timer != null) {
        clearInterval(tupelo.list_timer);
        tupelo.list_timer = null;
      }
      Cookies.remove("akey");
      tupelo.player = null;
      T.log(tupelo);
      dbg();
      return setState("initial", "fast");
    };
    gameCreateOk = function(result) {
      tupelo.game_id = result;
      T.log(tupelo);
      dbg();
      $("p#joined_game").html("joined game " + tupelo.game_id);
      setState("gameCreated", "fast");
      tupelo.event_fetch_timer = new T.Timer("/ajax/get_events", 2000, eventsOk, {
        data: {
          akey: tupelo.player.akey
        }
      });
      return updateLists();
    };
    cardPlayed = function(event) {
      var card, table;
      T.log("cardPlayed");
      table = $("#player_" + event.player.id + " .table");
      if (table.length === 0) {
        T.log("player not found!");
        return true;
      }
      card = new T.Card(event.card.suit, event.card.value);
      table.html("<span style=\"display: none;\" class=\"card\">" + card.toShortHtml() + "</span>");
      table.children().show(500);
      setTimeout(processEvent, 500);
      return false;
    };
    messageReceived = function(event) {
      var eventLog;
      T.log("messageReceived");
      eventLog = $("#event_log");
      eventLog.append(escapeHtml(event.sender) + ": " + escapeHtml(event.message) + "\n");
      eventLog.scrollTop(eventLog[0].scrollHeight - eventLog.height());
      return true;
    };
    clearTable = function() {
      clearTimeout(tupelo.clear_timeout);
      T.log("clearing table");
      $("#game_area .table").html("");
      $("#game_area table tbody").unbind("click");
      return tupelo.event_timer = setTimeout(processEvent, 0);
    };
    trickPlayed = function(event) {
      T.log("trickPlayed");
      $("#game_area table tbody").click(clearTable);
      tupelo.clear_timeout = setTimeout(clearTable, 5000);
      return false;
    };
    getTeamPlayers = function(team) {
      return [$("#table_" + team + " .player_name").html(), $("#table_" + (team + 2) + " .player_name").html()];
    };
    updateGameState = function(state) {
      var key, statusStr;
      statusStr = "";
      for (key in state) {
        if (!__hasProp.call(state, key)) continue;
        tupelo.game_state[key] = state[key];
      }
      if (state.status === T.VOTING) {
        statusStr = "VOTING";
      } else if (state.status === T.ONGOING) {
        if (state.mode === T.NOLO) {
          statusStr = "NOLO";
        } else {
          if (state.mode === T.RAMI) statusStr = "RAMI";
        }
      }
      statusStr = "<span>" + statusStr + "</span>";
      statusStr += "<span>tricks: " + state.tricks[0] + " - " + state.tricks[1] + "</span>";
      if (state.score != null) {
        if (state.score[0] > 0) {
          statusStr += "<span>score: " + escapeHtml(getTeamPlayers(0).join(" &amp; ")) + ": " + state.score[0] + "</span>";
        } else if (state.score[1] > 0) {
          statusStr += "<span>score: " + escapeHtml(getTeamPlayers(1).join(" &amp; ")) + ": " + state.score[1] + "</span>";
        } else {
          statusStr += "<span>score: 0</span>";
        }
      }
      $("#game_status").html(statusStr);
      if (state.turn_id != null) {
        $(".player_data .player_name").removeClass("highlight_player");
        $("#player_" + state.turn_id + " .player_name").addClass("highlight_player");
      }
      return dbg();
    };
    cardClicked = function(event) {
      var card, cardId;
      cardId = $(this).find(".card").attr("id").slice(5);
      card = tupelo.hand[cardId];
      T.log(card);
      if (card != null) {
        $.ajax({
          url: "/ajax/game/play_card",
          success: function(result) {
            tupelo.my_turn = false;
            $("#hand .card").removeClass("card_selectable");
            return getGameState();
          },
          error: function(xhr, astatus, error) {
            if (ajaxErr(xhr, astatus, error) !== true) {
              return window.alert(xhr.status + " " + error);
            }
          },
          data: {
            akey: tupelo.player.akey,
            game_id: tupelo.game_id,
            card: JSON.stringify(card)
          }
        });
      }
      return event.preventDefault();
    };
    updateHand = function(newHand) {
      var card, hand, html, i, item, _len;
      html = "";
      hand = [];
      for (i = 0, _len = newHand.length; i < _len; i++) {
        item = newHand[i];
        card = new T.Card(item.suit, item.value);
        hand.push(card);
        if (tupelo.my_turn) html += "<a class=\"selectable\" href=\"#\">";
        html += ("<span class=\"card\" id=\"card_" + i + "\">") + card.toShortHtml() + "</span>";
        if (tupelo.my_turn) html += "</a>";
      }
      tupelo.hand = hand;
      $("#hand").html(html);
      if (tupelo.my_turn) {
        $("#hand .card").addClass("card_selectable");
        return $("#hand a").click(cardClicked);
      }
    };
    getGameState = function() {
      return $.ajax({
        url: "/ajax/game/get_state",
        success: function(result) {
          T.log(result);
          if (result.game_state != null) updateGameState(result.game_state);
          if (result.hand != null) return updateHand(result.hand);
        },
        error: ajaxErr,
        data: {
          akey: tupelo.player.akey,
          game_id: tupelo.game_id
        }
      });
    };
    turnEvent = function(event) {
      T.log("turnEvent");
      tupelo.my_turn = true;
      getGameState();
      return true;
    };
    stateChanged = function(event) {
      T.log("stateChanged");
      if (event.game_state.status === T.VOTING) {
        startOk();
      } else if (event.game_state.status === T.ONGOING) {
        $("#game_area table tbody").click(clearTable);
        tupelo.clear_timeout = setTimeout(clearTable, 5000);
        return false;
      }
      return true;
    };
    processEvent = function() {
      var event, handled;
      handled = true;
      if (tupelo.events.length === 0) {
        T.log("no events to process");
        tupelo.event_timer = null;
        return;
      }
      event = tupelo.events.shift();
      if (event.game_state != null) updateGameState(event.game_state);
      switch (event.type) {
        case 1:
          handled = cardPlayed(event);
          break;
        case 2:
          handled = messageReceived(event);
          break;
        case 3:
          handled = trickPlayed(event);
          break;
        case 4:
          handled = turnEvent(event);
          break;
        case 5:
          handled = stateChanged(event);
          break;
        default:
          T.log("unknown event " + event.type);
      }
      if (handled === true) {
        return tupelo.event_timer = setTimeout(processEvent, 0);
      }
    };
    eventsOk = function(result) {
      /*
          if (result.length > 0)
            eventLog = $("#event_log")
            eventLog.append(JSON.stringify(result) + "\n")
            eventLog.scrollTop(eventLog[0].scrollHeight - eventLog.height())
      */
      var event, _i, _len;
      for (_i = 0, _len = result.length; _i < _len; _i++) {
        event = result[_i];
        tupelo.events.push(event);
      }
      if (tupelo.events.length > 0 && !(tupelo.event_timer != null)) {
        tupelo.event_timer = setTimeout(processEvent, 0);
      }
      return dbg();
    };
    gameInfoOk = function(result) {
      var i, index, myIndex, pl, _len, _len2;
      T.log("gameInfoOk");
      T.log(result);
      myIndex = 0;
      for (i = 0, _len = result.length; i < _len; i++) {
        pl = result[i];
        if (pl.id === tupelo.player.id) {
          myIndex = i;
          break;
        }
      }
      for (i = 0, _len2 = result.length; i < _len2; i++) {
        pl = result[i];
        index = (4 + i - myIndex) % 4;
        $("#table_" + index + " .player_data").attr("id", "player_" + pl.id);
        $("#player_" + pl.id + " .player_name").html(escapeHtml(pl.player_name));
      }
    };
    startOk = function(result) {
      if (tupelo.list_timer != null) {
        clearInterval(tupelo.list_timer);
        tupelo.list_timer = null;
      }
      $("#event_log").html("");
      setState("inGame");
      $.ajax({
        url: "/ajax/game/get_info",
        success: gameInfoOk,
        error: ajaxErr,
        data: {
          game_id: tupelo.game_id
        }
      });
      getGameState();
      return dbg();
    };
    updateLists = function() {
      $.ajax({
        url: "/ajax/game/list",
        success: listGamesOk,
        error: ajaxErr
      });
      return $.ajax({
        url: "/ajax/player/list",
        success: listPlayersOk,
        error: ajaxErr,
        data: {
          akey: tupelo.player.akey
        }
      });
    };
    $("#echo_ajax").click(function() {
      var text;
      text = $("#echo").val();
      return $.ajax({
        url: "/ajax/echo",
        data: {
          test: text
        },
        success: function(result) {
          $("#echo_result").html(escapeHtml(result));
          return $("#echo").val("");
        },
        error: ajaxErr
      });
    });
    $("#register_btn").click(function() {
      var input, name;
      input = $("#register_name");
      name = input.val();
      if (!name || input.hasClass("initial")) {
        alert("Please enter your name first");
        return;
      }
      tupelo.player = new T.Player(name);
      T.log(tupelo);
      return $.ajax({
        url: "/ajax/player/register",
        data: {
          player: JSON.stringify(tupelo.player)
        },
        success: registerOk,
        error: ajaxErr
      });
    });
    $("#register_name").keyup(function(event) {
      if ((event.keyCode || event.which) === 13) return $("#register_btn").click();
    });
    $("#register_name").focus(function(event) {
      if ($(this).hasClass("initial")) {
        $(this).val("");
        return $(this).removeClass("initial");
      }
    });
    $("#quit_btn").click(function() {
      return $.ajax({
        url: "/ajax/player/quit",
        data: {
          akey: tupelo.player.akey
        },
        success: quitOk,
        error: function(xhr, astatus, error) {
          if (ajaxErr(xhr, astatus, error) === true) return quitOk();
        }
      });
    });
    $(".game_leave_btn").click(function() {
      return $.ajax({
        url: "/ajax/game/leave",
        data: {
          akey: tupelo.player.akey,
          game_id: tupelo.game_id
        },
        success: leaveOk,
        error: function(xhr, astatus, error) {
          if (ajaxErr(xhr, astatus, error) === true) return leaveOk();
        }
      });
    });
    $("#game_create_btn").click(function() {
      return $.ajax({
        url: "/ajax/game/create",
        data: {
          akey: tupelo.player.akey
        },
        success: gameCreateOk,
        error: ajaxErr
      });
    });
    $("#game_start").click(function() {
      return $.ajax({
        url: "/ajax/game/start",
        data: {
          akey: tupelo.player.akey,
          game_id: tupelo.game_id
        },
        success: startOk,
        error: ajaxErr
      });
    });
    $("#game_start_with_bots").click(function() {
      return $.ajax({
        url: "/ajax/game/start_with_bots",
        data: {
          akey: tupelo.player.akey,
          game_id: tupelo.game_id
        },
        success: startOk,
        error: ajaxErr
      });
    });
    if (T.debug === true) {
      $("#debug").click(function() {
        return $(this).toggle();
      });
    } else {
      $("#debug").hide();
    }
    $(window).unload(function() {
      if (tupelo.game_id != null) {
        return $.ajax({
          url: "/ajax/game/leave",
          async: false,
          data: {
            akey: tupelo.player.akey,
            game_id: tupelo.game_id
          }
        });
      }
    });
    window.onbeforeunload = function(e) {
      var msg;
      if (!(tupelo.game_id != null)) return undefined;
      e = e || window.event;
      msg = "By leaving the page you will also leave the game.";
      if (e) e.returnValue = msg;
      return msg;
    };
    hello();
    return setState("initial");
  });

}).call(this);
