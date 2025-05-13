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
