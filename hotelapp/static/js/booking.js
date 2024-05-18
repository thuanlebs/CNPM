let cart = [];
let room_types = [];
let rooms = [];
const cartItemList = $(".cart-list");
const totalCart = $(".badge");
const total = $(".total");

// Cart modal actions
cartItemList.addEventListener("click", (e) => {
  e.preventDefault();
  const target = e.target;
  const room_id = target.closest(".cart-item").dataset.room;

  if (e.target.getAttribute("href")) {
    window.location.href = e.target.getAttribute("href");
  } else if (target.classList.contains("cart-trash")) {
    const confirmBtn = $(".confirm");
    confirmBtn.addEventListener("click", () => {
      fetch(`/api/cart/${room_id}`, {
        method: "delete",
      })
        .then((res) => {
          loading();
          if (!res.ok) {
            throw new Error(
              `Failed to delete room from cart. Status: ${res.status}`
            );
          }
          return res.json();
        })
        .then((data) => {
          cartChanges(data);
        });
    });
  }
});

const renderCart = () => {
  cartItemList.innerHTML = "";
  if (cart?.length > 0) {
    cart.forEach((item) => {
      const newItem = document.createElement("article");
      newItem.classList.add("cart-item");
      newItem.dataset.room = item.room;

      const info = room_types.find((room) => room.id == item.room_type);

      newItem.innerHTML = cartItemComponent(rooms, item, info);
      cartItemList.appendChild(newItem);
    });
  }
  initJsToggle();
};

const cartChanges = async (data) => {
  cart = await data.items;
  setTimeout(() => {
    totalCart.innerHTML = cart?.length ?? 0;
    renderCart();
    total.innerHTML = `$${data.total_amount}`;
  }, 500);
};

const goToDetail = (id) => {
  fetch(`/api/room_types/${id}`)
    .then((response) => response.json())
    .then((res) => {
      const room = res.data;

      $("#room-detail").innerHTML = roomComponent(room);

      $(".room-detail__back").addEventListener("click", () => {
        toggleDisplay($("#room-items"));
        toggleDisplay($("#room-detail"));
      });
    });
};

const format = (value) => {
  return value.toString().length === 1 ? `0${value}` : value;
};

function formatDate(inputDate) {
  var date = new Date(inputDate);
  if (!isNaN(date.getTime())) {
    // Months use 0 index.
    return (
      date.getMonth() + 1 + "/" + date.getDate() + "/" + date.getFullYear()
    );
  }
}

const setValidCheckOut = () => {
  // Parse the date values into Date objects
  const currentCheckIN = new Date(checkIn.value);
  const currentCheckOut = new Date(checkOut.value);

  // Ensure currentCheckOutis at least one day after currentCheckIN
  if (currentCheckOut <= currentCheckIN) {
    currentCheckIN.setDate(currentCheckIN.getDate() + 1);
    currentCheckIN.setMonth(currentCheckIN.getMonth() + 1);
    const date = format(currentCheckIN.getDate());
    const month = format(currentCheckIN.getMonth());
    checkOut.value = `${currentCheckIN.getFullYear()}-${month}-${date}`;
  }
};

const toggleDisplay = (target) => {
  const isHidden = target.classList.contains("hide");
  requestAnimationFrame(() => {
    target.classList.toggle("hide", !isHidden);
    target.classList.toggle("show", isHidden);
  });
};

const roomComponent = (room) => {
  return `
  <h2 class="room-detail__heading">
    <button
      class="room-detail__back"
    >
      <i class="fa-solid fa-arrow-left"></i>
    </button>
    <span class="room-detail__title"> ${room.name} </span>
  </h2>
  
  <div class="separate"></div>
  
  <img
    src="/static/img/${room.images[0]}"
    width="500"
    alt="room-img"
  />
  
  <div class="room-info">
    <div class="title">
      <strong>More info</strong>
    </div>
    <div class="description">
      Room Size ${room.room_size} m².<br />
      This suite features a balcony, minibar and bathrobe.
    </div>
  </div>
  
  <div class="room-info">
    <div class="title">
      <strong>People Available</strong>
    </div>
    <div class="description">${room.adults} Adults, 1 Children</div>
  </div>
  
  <div class="room-info">
    <div class="title">
      <strong>Bed room</strong>
    </div>
    <div class="description">
      Bed:
      ${room.grouped[7].map((item) => item.name)}
    </div>
  </div>
  
  <div class="room-info">
    <div class="title">
      <strong>Room Amenities</strong>
    </div>
    <div class="description">
      <ul style="margin: 0px; padding: 0px">
        <li class="list-inline-item">
          <strong>Bedroom</strong>: ${room.grouped[6].map((item) => item.name)}
        </li>
        <li class="list-inline-item">
          <strong>Bath room</strong>: ${room.grouped[1].map(
            (item) => item.name
          )}
        </li>
        <li class="list-inline-item">
          <strong>Services </strong>: ${room.grouped[5].map(
            (item) => item.name
          )}
        </li>
      </ul>
    </div>
  </div>`;
};

const cartItemComponent = (rooms, item, info) => {
  return `
  <a href="/" class="cart-item__img">
  <img
    src="/static/img/${info.images[0]}"
    class="cart-item__thumb"
    alt=""
  />
</a>
<div class="cart-item__info">
  <div class="cart-item__info-left">
    <h3 class="cart-item__title">
      <a href="/"> ${info.name} </a>
    </h3>
    <p class="cart-item__price-wrap">Capacity: ${info.adults} adults</p>
    <div class="cart-item__ctrl cart-item__ctrl--md-block">
      <div class="cart-item__input">
        <span>Room: </span>
        <span>${rooms.find((room) => room.id === item.room)?.name}</span>
      </div>
    </div>
  </div>
  <div class="cart-item__info-right">
    <p class="cart-item__total-price">$${info.price}</p>
    <div class="cart-item__ctrl">
      <button
        class="cart-item__ctrl-btn cart-trash js-toggle"
        toggle-target="#delete-confirm"
        >
        <i class="fa-solid fa-trash"></i>
        Delete
      </button>
    </div>
  </div>
</div> `;
};

// Initialize booking page
const initPage = () => {
  // get data
  fetch("/api/room_types")
    .then((response) => response.json())
    .then((data) => {
      room_types = data.data;
    });

  fetch("/api/rooms")
    .then((response) => response.json())
    .then((data) => {
      rooms = data.data;
    });

  fetch("/api/cart")
    .then((res) => res.json())
    .then((data) => {
      cartChanges(data);
    });

  $$(".btn-detail").forEach((item) => {
    item.addEventListener("click", () => {
      goToDetail(parseInt(item.closest(".room-item").dataset.id));
      toggleDisplay($(".room-items"));
    });
  });

  // Add to cart action
  $$(".add-to-cart").forEach((item) => {
    item.addEventListener("click", () => {
      fetch("/api/cart", {
        method: "post",
        body: JSON.stringify({
          id: item.closest(".room-item").dataset.id,
          checkIn: checkIn.value,
          checkOut: checkOut.value,
        }),

        headers: {
          "Content-Type": "application/json",
        },
      })
        .then((res) => res.json())
        .then((data) => {
          cartChanges(data);
        });

      const alert = $(".alert");
      alert.classList.add("show");

      setTimeout(() => {
        alert.classList.remove("show");
        alert.classList.add("hide");
      }, 1000);
    });
  });
};

initPage();
