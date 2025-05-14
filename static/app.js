function logout() {
  $.ajax({
    type: "POST",
    url: "/users/logout",
    success: function () {
      window.location.href = "/";
    },
  });
}

$(".deleteForm").submit(function (event) {
  let confirmed = confirm("정말 삭제하시겠습니까?");
  if (!confirmed) {
    event.preventDefault();
  }
});

$(".confirmForm").submit(function (event) {
  let confirmed = confirm(
    "정말 확정하시겠습니까? 파티를 확정할 시 추가 인원을 모집할 수 없습니다."
  );
  if (!confirmed) {
    event.preventDefault();
  }
});

$(".exitForm").submit(function (event) {
  let confirmed = confirm("정말 퇴장하시겠습니까?");
  if (!confirmed) {
    event.preventDefault();
  }
});

function join(room_id) {
  $.ajax({
    type: "POST",
    url: "/rooms/join",
    data: { room_id },
    success: function (response) {
      alert(response.message);
      window.location.reload();
    },
  });
}

function exit(room_id) {
  $.ajax({
    type: "POST",
    url: "/rooms/exit",
    data: { room_id },
    success: function (response) {
      alert(response.message);
      window.location.reload();
    },
  });
}
