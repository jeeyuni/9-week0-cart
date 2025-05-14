document.addEventListener("DOMContentLoaded", () => {
  const titles = {
    "파티 만들기": "navbarMakeParty",
    "신청한 파티": "navbarUsersRooms",
    "파티 찾기": "navbarRooms",
    "파티 수정하기": "navbarUsersRooms",
    "파티 세부사항": "navbarUsersRooms",
  };

  const newID = titles[document.title];
  document.getElementById(newID)?.classList.add("active");
});
