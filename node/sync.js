class Sync {
  constructor(size, key) {
    this.size = size;
    this.key = key;
    this.cache = [];
    this.set = new Set();
  }

  push(one) {
    const key = this.key;
    this.set.add(one[key]);
    this.cache.push(one);
    this.cache.sort( (a, b) => {
      //console.log(a[key], b[key])
      return a[key] - b[key];
    });
    // console.log('size', this.set.size);
    let res = [];
    if (this.set.size > this.size) {
      const pop_id = this.cache[0][key];
      let idx = 0;
      this.set.delete(pop_id);
      for (let i in this.cache) {
        const ele = this.cache[i];
        if (ele[key] == pop_id) {
          idx = idx+1;
        } else {
          break
        }
      }
      res = this.cache.slice(0,idx);
      console.log('sync res size', res.length);
      this.cache = this.cache.slice(idx,);
    }
    return res
  }
}

exports = module.exports = Sync;