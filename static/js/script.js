var question;
var playing = true;

$(document).ready(function() {
  if ($("#startTime")) {
    let setMinutes = parseInt($("#startTime").val());
    display = document.querySelectorAll(".timer");
    startTimer(setMinutes, display);
  }
});

function redirect() {
//  location.replace($("#gameover").val());
  location.reload();
}

function startTimer(duration, display) {
  let timer = duration,
    minutes, seconds;
  let intervalLoop = setInterval(function() {
    seconds = timer;
    seconds = seconds < 10 ? "0" + seconds : seconds;
    for (let i = 0; i < display.length; i++) {
      display[i].textContent = seconds;
    }
    if (--timer < 0) {
      for (let i = 0; i < display.length; i++) {
        redirect();
      }
      clearInterval(intervalLoop);
    }
  }, 1000);
}

$( "#sound-toggle" ).change(function(event) {
  event.preventDefault();
  submitFormAJAX( $( "#sound_form" )[0], null );
});

$( ".game-time" ).change(function(event) {
  $( "div.leaderboard" ).each((index, board=this) => {
    if (((index + 2) * 30) != $( this ).val()) {
      $( board ).addClass("hide");
    } else {
      $( board ).removeClass("hide");
    }
  });
});

// Clears the player name field on click
$("#quiz_player_form .player-name").click(function() {
  $(this).val('');
});

// Triggered when answer is submitted
$("#quiz_form input[name='answer']").change(function(event) {
  //Player has selected so disable the other options
  $("#quiz_form input[name='answer']:not(:checked)").prop('disabled', true);
  //Submit the answer to the server
  submitFormAJAX($("#quiz_form")[0], checkAnswerCallback);
});

function next_question() {
  if (playing) {
    //Fill out new question text
    $(".quiz-question").text(question.question);
    $(".quiz-option").each(function(index) {
      $(this).children("div").text(question.options[index]);
    });

    //Reset radio radiobuttons
    $("#quiz_form input[name='answer']").prop('disabled', false);
    $("#quiz_form input[name='answer']").prop('checked', false);

    //Reset button highlighting
    $(".quiz-option").each(function(index) {
      $(this).removeClass("wrong").removeClass("correct");
    });

    //Hide the next question button
  //  $("#next_question_btn").addClass("hide");
  } else {
    location.reload();
  }
}

// Shows the next quiz question
$("#next_question_btn").click(function(event) {
  event.preventDefault();
  next_question();
});

//AJAX answer check callback
function checkAnswerCallback(response) {
  let score = response.player_score;
  let scoreModulus = score % 5;
  let lastScore = scoreModulus - 1;
  question = response.next_question;

  // Show the next question button
  //$("#next_question_btn").removeClass("hide");

  //wait a second before showing the next question
  setTimeout(function() {
    next_question();
  }, 1000);

  $(".quiz-option").each(function(index) {
    if (index == response.correct_answer) {
      $(this).addClass("correct");
    } else {
      $(this).addClass("wrong");
    }
  });

  if (response.player_correct) {
    // Update pint glass
    if (scoreModulus > 0) {
      $("#pint").effect("bounce", "slow").removeClass(`pint${lastScore}`).addClass(`pint${scoreModulus}`);
    } else {
      $("#pint").effect("bounce", "slow").removeClass("pint4").addClass("pint5");
      $("#pint").effect("drop", 'fast');
      setTimeout(function() {
        $("#pint").removeClass("pint5").addClass("pint0");
        $("#pint").effect("slide", "fast");
      }, 1000);
      // A pint has been finished, add a score
      $("#pint_counter").append(`
        <div class="add-pint">
          <img src="/static/images/pint-counter-icon.svg">
        </div>
      `);
    }
    //play drink sfx
    if ($( "#sound-toggle" ).prop("checked")) {
      $("#drink_sound")[0].play();
    }
  } else {
    if ($( "#sound-toggle" ).prop("checked")) {
      $("#feck_sound")[0].play();
    }
  }
}

/*
 * General function for submitting forms via AJAX
 */
function submitFormAJAX(form, callbackSuccess) {
  // Get form data
  var data = new FormData(form);
  var serialised = {};
  // serialise it into key/value pairs that can be converted to JSON
  for (var key of data.keys()) {
    serialised[key] = data.get(key);
  }
  // Make AJAX request
  $.ajax({
    type: "POST",
    url: $(form).attr("action"), // Get route from form attribute
    contentType: 'application/json;charset=UTF-8',
    data: JSON.stringify(serialised),
    success: callbackSuccess
  });
}
