Array.from(document.getElementsByClassName("testplugin")).forEach((el) => {
  if (el.getContext) {
    let ctx = el.getContext('2d');
    ctx.moveTo(0, 0);
    ctx.lineTo(200, 100);
    ctx.stroke();
  }
})
