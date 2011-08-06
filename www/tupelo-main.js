/* tupelo-main.js
 * vim: sts=4 sw=4 et:
*/
/*jslint devel: true, browser: true, sloppy: true, maxerr: 50, indent: 4 */

$(document).ready(function () {
    // status object
    var tupelo = {game_state: {}, events: []};

    var states = {
        initial: {show: ["#register_form"],
            hide: ["#quit_form", "#games", "#my_game", "#game"],
            change: function () {
                var reg;
                reg = $("#register_name");
                reg.addClass("initial");
                reg.val("Your name");
            }
            },
        registered: {show: ["#quit_form", "#games", "#game_create_form"],
            hide: ["#register_form"]
            },
        gameCreated: {show: ["#my_game"],
            hide: ["#game_create_form"]
            },
        inGame: {show: ["#game"],
            hide: ["#games", "#my_game"]
            }
    };

    function setState(state, effectDuration) {
        var i, st = states[state];
        for (i = 0; i < st.hide.length; i++) {
            $(st.hide[i]).hide(effectDuration);
        }
        for (i = 0; i < st.show.length; i++) {
            $(st.show[i]).show(effectDuration);
        }
        if (st.change !== undefined) {
            st.change();
        }
    }

    function escapeHtml(str) {
        return str.replace("<", "&lt;").replace(">", "&gt;");
    }

    function dbg() {
        if (T.debug === true) {
            $("#debug").html(JSON.stringify(tupelo));
        }
    }

    function ajaxErr(xhr, astatus, error) {
        var jsonErr, handled = false;
        // 403 is for game and rule errors
        if (xhr.status == 403) {
            // parse from json
            jsonErr = eval("(" + xhr.responseText + ")");
            if (jsonErr.message !== undefined) {
                window.alert(jsonErr.message);
                handled = true;
            }
        } else {
            T.log("status: " + astatus);
            T.log("error: " + error);
        }
        return handled;
    }

    function updateGameLinks(disabledIds) {
        var gameJoinClicked = function (elem) {
            // "game_join_ID"
            var game_id = elem.target.id.slice(10);
            T.log("joining game " + game_id);
            $.ajax({url: "/ajax/game/enter",
                data: {akey: tupelo.player.akey, game_id: game_id},
                success: gameCreateOk, error: ajaxErr});

        };
        var i;
        // update game links
        if (tupelo.game_id !== undefined) {
            $("button.game_join").attr("disabled", true);
            $("tr#game_id_" + tupelo.game_id).addClass("highlight");
        } else {
            for (i = 0; i < disabledIds.length; i++) {
                $("button#" + disabledIds[i]).attr("disabled", true);
            }
            $("button.game_join").click(gameJoinClicked);
        }
    }

    function listGamesOk(result) {
        //T.log("listGamesOk");
        //T.log(result);
        var html = "<table>", disabledIds = [], game_id, i, plr;
        for (game_id in result) {
            if (result.hasOwnProperty(game_id)) {
                html += "<tr id=\"game_id_" + game_id + "\"><td>" + game_id + "</td>";
                var players = [];
                for (i = 0; i < result[game_id].length; i++) {
                    plr = new T.Player().fromObj(result[game_id][i]);
                    players.push(plr.player_name);
                    //T.log(player);
                }
                //html += "<td>" + JSON.stringify(result[game_id]) + "</td>";
                html += "<td>" + escapeHtml(players.join(", ")) + "</td>";
                html += "<td><button class=\"game_join\" id=\"game_join_" + game_id + "\">join</button></td>";
                html += "</tr>";
                if (players.length == 4) {
                    disabledIds.push("game_join_" + game_id);
                }
            }
        }
        html += "</table>";
        $("#game_list").html(html);
        updateGameLinks(disabledIds);
        dbg();
    }

    function registerOk(result) {
        $("#name").val("");
        tupelo.player.id = result.player_id;
        tupelo.player.akey = result.akey;
        T.log(tupelo);
        dbg();
        // clear game list if there was one previously
        $("#game_list").html("");
        $(".my_name").html(escapeHtml(tupelo.player.player_name));
        setState("registered", "fast");
        listGames();
        T.log("creating timer");
        tupelo.game_list_timer = new T.Timer("/ajax/game/list", 5000, listGamesOk);
        T.log("timer created");
    }

    function quitOk(result) {
        if (tupelo.game_list_timer !== undefined) {
            tupelo.game_list_timer.disable();
            tupelo.game_list_timer = undefined;
        }
        if (tupelo.event_fetch_timer !== undefined) {
            tupelo.event_fetch_timer.disable();
            tupelo.event_fetch_timer = undefined;
        }
        if (tupelo.event_timer !== undefined) {
            tupelo.event_timer.disable();
            tupelo.event_timer = undefined;
        }
        tupelo.player = undefined;
        tupelo.game_id = undefined;
        tupelo.game_state = {};
        tupelo.hand = undefined;
        tupelo.my_turn = undefined;
        T.log(tupelo);
        dbg();
        setState("initial", "fast");
    }

    function gameCreateOk(result) {
        tupelo.game_id = result;
        T.log(tupelo);
        dbg();
        $("p#joined_game").html("joined game " + tupelo.game_id);
        setState("gameCreated", "fast");
        listGames();
    }

    function cardPlayed(event) {
        T.log("cardPlayed");
        //T.log(event);
        var table = $("#player_" + event.player.id + " .table");
        if (table.length == 0) {
            T.log("player not found!");
            return true;
        }
        //table.hide();
        var card = new T.Card(event.card.suit, event.card.value);
        table.html("<span style=\"display: none;\" class=\"card\">" + card.toShortHtml() + "</span>");
        table.children().show(500);
        setTimeout(processEvent, 500);
        return false;
    }

    function messageReceived(event) {
        T.log("messageReceived");
        var eventLog = $("#event_log");
        eventLog.append(escapeHtml(event.sender) + ": " + escapeHtml(event.message) + "\n");
        eventLog.scrollTop(eventLog[0].scrollHeight - eventLog.height());
        return true;
    }

    // clear the table and resume event processing
    // called either from timeout or click event
    function clearTable() {
        clearTimeout(tupelo.clear_timeout);
        T.log("clearing table");
        $("#game_area .table").html("");
        $("#game_area table tbody").unbind("click");
        // re-enable event processing
        tupelo.event_timer = setTimeout(processEvent, 0);
        //T.log("trickPlayed: set event_timer to " + tupelo.event_timer);
    }

    function trickPlayed(event) {
        T.log("trickPlayed");
        // TODO: highlight the highest card
        // allow the user to clear the table and proceed by clicking the table
        $("#game_area table tbody").click(clearTable);
        // setting timeout to show the played trick for a longer time
        tupelo.clear_timeout = setTimeout(clearTable, 5000);
        return false; // this event is not handled yet
    }

    function updateGameState(state) {
        var statusStr = "", key;
        for (key in state) {
            if (state.hasOwnProperty(key)) {
                tupelo.game_state[key] = state[key];
            }
        }
        // show game status (voting, nolo, rami)
        if (state.state == T.VOTING) { // 1
            statusStr = "VOTING";
        } else if (state.state == T.ONGOING) { // 2
            if (state.mode == T.NOLO) {
                statusStr = "NOLO";
            } else if (state.mode == T.RAMI) {
                statusStr = "RAMI";
            }
        }
        statusStr = "<span class=\"status\">" + statusStr + "</span>";
        $("#game_status").html(statusStr);

        // highlight the player in turn
        if (state.turn_id !== undefined) {
            $(".player_data .player_name").removeClass("highlight_player");
            $("#player_"  + state.turn_id + " .player_name").addClass("highlight_player");
        }
        dbg();
    }

    function cardClicked(event) {
        //T.log("cardClicked()");
        // id is "card_X"
        var cardId = $(this).find(".card").attr("id").slice(5);
        var card = tupelo.hand[cardId];
        T.log(card);
        if (card !== undefined) {
            $.ajax({url: "/ajax/game/play_card",
                success: function (result) {
                    tupelo.my_turn = false;
                    $("#hand .card").removeClass("card_selectable");
                    getGameState();
                },
                error: function (xhr, astatus, error) {
                    if (ajaxErr(xhr, astatus, error) !== true) {
                        window.alert(xhr.status + " " + error);
                    }
                },
                data: {akey: tupelo.player.akey, game_id: tupelo.game_id,
                    card: JSON.stringify(card)}});
        }
        event.preventDefault();
    }

    function updateHand(newHand) {
        var i, card, html = "";
        var hand = [];
        for (i = 0; i < newHand.length; i++) {
            card = new T.Card(newHand[i].suit, newHand[i].value);
            hand.push(card);
            if (tupelo.my_turn) {
                html += "<a class=\"selectable\" href=\"#\">";
            }
            html += "<span class=\"card\" id=\"card_" + i + "\">" + card.toShortHtml() + "</span>";
            if (tupelo.my_turn) {
                html += "</a>";
            }
        }
        tupelo.hand = hand;
        $("#hand").html(html);
        if (tupelo.my_turn) {
            $("#hand .card").addClass("card_selectable");
            $("#hand a").click(cardClicked);
        }
    }

    function getGameState() {
        $.ajax({url: "/ajax/game/get_state",
            success: function (result) {
                T.log(result);
                if (result.game_state !== undefined) {
                    updateGameState(result.game_state);
                }
                if (result.hand !== undefined) {
                    updateHand(result.hand);
                }
            },
            error: ajaxErr,
            data: {akey: tupelo.player.akey, game_id: tupelo.game_id}});
    }

    function turnEvent(event) {
        T.log("turnEvent");
        tupelo.my_turn = true; // enables click callbacks for cards in hand
        getGameState();
        return true;
    }

    function stateChanged(event) {
        T.log("stateChanged");
        if (event.game_state.state == T.ONGOING) { // VOTING -> ONGOING
            // allow the user to clear the table and proceed by clicking the table
            $("#game_area table tbody").click(clearTable);
            // setting timeout to show the voted cards for a longer time
            tupelo.clear_timeout = setTimeout(clearTable, 5000);
            return false;
        }
        return true;
    }

    function processEvent() {
        var handled = true, event;
        //T.log("processEvent " + tupelo.event_timer);
        if (tupelo.events.length == 0) {
            T.log("no events to process");
            tupelo.event_timer = undefined;
            return;
        }
        event = tupelo.events.shift();
        if (event.game_state !== undefined) {
            updateGameState(event.game_state);
        }
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
                break;
        }
        if (handled === true) {
            tupelo.event_timer = setTimeout(processEvent, 0);
        }
    }

    function eventsOk(result) {
        var i;
        /*
        if (result.length > 0) {
            var eventLog = $("#event_log");
            eventLog.append(JSON.stringify(result) + "\n");
            eventLog.scrollTop(eventLog[0].scrollHeight - eventLog.height());
        }
        */
        // push events to queue
        for (i = 0; i < result.length; i++) {
            tupelo.events.push(result[i]);
        }
        // schedule event processing if needed
        if (tupelo.events.length > 0 && tupelo.event_timer === undefined) {
            tupelo.event_timer = setTimeout(processEvent, 0);
        }
        dbg();
    }

    function gameInfoOk(result) {
        T.log("gameInfoOk");
        T.log(result);
        var html, i, myIndex = 0, pl, index;
        // find my index
        for (i = 0; i < result.length; i++) {
            if (result[i].id == tupelo.player.id) {
                myIndex = i;
                break;
            }
        }
        for (i = 0; i < result.length; i++) {
            pl = result[i];
            // place where the player goes when /me is always at the bottom
            index = (4 + i - myIndex) % 4;
            // set player id and name
            $("#table_" + index + " .player_data").attr("id", "player_" + pl.id);
            $("#player_" + pl.id + " .player_name").html(escapeHtml(pl.player_name));
        }
    }

    function startOk(result) {
        if (tupelo.game_list_timer !== undefined) {
            tupelo.game_list_timer.disable();
            tupelo.game_list_timer = undefined;
        }
        $("#event_log").html("");
        setState("inGame");
        $.ajax({url: "/ajax/game/get_info",
            success: gameInfoOk, error: ajaxErr, data: {game_id: tupelo.game_id}});
        getGameState();
        tupelo.event_fetch_timer = new T.Timer("/ajax/get_events", 2000,
            eventsOk, {data: {akey: tupelo.player.akey}});
        dbg();
    }

    function listGames() {
        $.ajax({url: "/ajax/game/list",
            success: listGamesOk, error: ajaxErr});
    }

    $("#echo_ajax").click(function () {
        //T.log("klik");
        var text = $("#echo").val();
        $.ajax({url: "/ajax/echo", data: {test: text},
            success: function (result) {
                $("#echo_result").html(escapeHtml(result));
                $("#echo").val("");
            }, error: ajaxErr});
    });

    $("#register_ajax").click(function () {
        var input = $("#register_name");
        var name = input.val();
        if (! name || input.hasClass("initial")) {
            alert("Please enter your name first");
            return;
        }
        tupelo.player = new T.Player(name);
        T.log(tupelo);
        $.ajax({url: "/ajax/player/register", data: {player: JSON.stringify(tupelo.player)},
            success: registerOk, error: ajaxErr});
    });
    // sign in by pressing enter
    $("#register_name").keyup(function (event) {
        if ((event.keyCode || event.which) == 13) {
            $("#register_ajax").click();
        }
    });

    $("#register_name").focus(function (event) {
        if ($(this).hasClass("initial")) {
            $(this).val("");
            $(this).removeClass("initial");
        }
    });

    $("#quit_ajax").click(function () {
        // TODO: should we cancel timers already here?
        $.ajax({url: "/ajax/player/quit", data: {akey: tupelo.player.akey},
            success: quitOk, error: function (xhr, astatus, error) {
                if (ajaxErr(xhr, astatus, error) == true) {
                    quitOk();
                }
            }});
    });

    $("#game_create_ajax").click(function () {
        $.ajax({url: "/ajax/game/create", data: {akey: tupelo.player.akey},
            success: gameCreateOk, error: ajaxErr});
    });

    $("#game_start").click(function () {
        $.ajax({url: "/ajax/game/start", data: {akey: tupelo.player.akey, game_id: tupelo.game_id},
            success: startOk, error: ajaxErr});
    });

    $("#game_start_with_bots").click(function () {
        $.ajax({url: "/ajax/game/start_with_bots", data: {akey: tupelo.player.akey, game_id: tupelo.game_id},
            success: startOk, error: ajaxErr});
    });

    if (T.debug === true) {
        $("#debug").click(function () { $(this).toggle(); });
    } else {
        $("#debug").hide();
    }

    setState("initial");
});
