function logout() {
  $.ajax({
    type: "POST",
    url: "/users/logout",
    success: function () {
      document.cookie =
        "token=; expires=Thu, 01 Jan 1970 00:00:00 GMT; path=/; SameSite=Strict";
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
  let confirmed = confirm("정말 확정하시겠습니까?");
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

// function join(rooms_id) {
//   $.ajax({
//     type: "POST",
//     url: "/rooms/join",
//     data: { rooms_id },
//   });
// }
