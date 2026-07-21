/* ************************************************************************** */
/*                                                                            */
/*                                                        :::      ::::::::   */
/*   ft_ten_queens_puzzle.c                             :+:      :+:    :+:   */
/*                                                    +:+ +:+         +:+     */
/*   By: q- <q-@student.42.fr>                      +#+  +:+       +#+        */
/*                                                +#+#+#+#+#+   +#+           */
/*   Created: 2026/07/21 02:29:22 by q-                #+#    #+#             */
/*   Updated: 2026/07/21 13:59:03 by q-               ###   ########.fr       */
/*                                                                            */
/* ************************************************************************** */

int glob = 14;
#include <unistd.h>

static int	absolute(int b)
{
	if (b < 0)
		return (-b);
	else
		return (b);
}

static void	print_position(int *board)
{
	int	i;

	i = 0;
	while (i < glob)
		write(1, &(char){board[i++] + '0'}, 1);
	write(1, "\n", 1);
}

static	int	is_valid(int *board, int col, int row)
{
	int	i;

	i = 0;
	while (i < col)
	{
		if (board[i] == row
			|| (absolute(i - col) == absolute(row - board[i])))
			return (0);
		i++;
	}
	return (1);
}

static void	place(int *board, int col, int *pos)
{
	int	row;

	row = 0;
	if (col == glob)
		return ;
	while (row < glob)
	{
		if (is_valid(board, col, row))
		{
			board[col] = row;
			if (col == glob - 1)
			{
				(*pos)++;
				// print_position(board);
				break ;
			}
			place(board, col + 1, pos);
		}
		row++;
	}
}

int	ft_ten_queens_puzzle(void)
{
	int	pos;
	int	chess_board[glob];

	pos = 0;
	place(chess_board, 0, &pos);
	return (pos);
}
#include <stdio.h>

int	main()
{
	printf("%d\n", ft_ten_queens_puzzle());
}