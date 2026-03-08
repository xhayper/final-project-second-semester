- Optimize item on belt logic
  - Check current grid, if exist, YIPPE, if not, aw
  - Item check grid from from (position.x - grid_size, position.y - grid_size, grid_size _ 3, grid_size _ 3) then use rect overlap, skip current grid
  - ^ Maybe smaller padding like (grid_size / 4)

- Add more machine

- Add machine class

- Add belt class

- Debug and optimize,get O(N) with location mapping